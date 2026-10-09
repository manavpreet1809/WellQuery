import time
import requests
from mlflow.tracking import MlflowClient

try:
    from databricks.sdk.runtime import dbutils
except Exception:
    dbutils = None

RETRIEVER_MODEL = "workspace.med.medibot_retriever"
CLASSIFIER_MODEL = "workspace.med.medibot_classifier"
RETRIEVER_ENDPOINT = "medibot-retriever"
CLASSIFIER_ENDPOINT = "medibot-classifier"

client = MlflowClient()

def get_workspace_host_and_token():
    if dbutils is None:
        raise RuntimeError("dbutils is not available.")

    ctx = dbutils.notebook.entry_point.getDbutils().notebook().getContext() # get notebook context
    host = ctx.apiUrl().get() # get API URL
    token = ctx.apiToken().get() # get API token
    
    return host, token

def get_latest_uc_model_version(model_fqn: str) -> int:
    versions = client.search_model_versions(f"name='{model_fqn}'") # list all versions

    if not versions:
        raise RuntimeError(f"No versions found for model: {model_fqn}")
    
    return max(int(v.version) for v in versions) # choose the highest value

# wait until the new model version is registered and usable
def wait_model_version_ready(model_fqn: str, version: int, timeout_seconds: int = 300):
    t0 = time.time() 

    while True:
        mv = client.get_model_version(model_fqn, str(version))
        status = (mv.status or "").upper() # fetch model version info
        
        if status == "READY":
            return
        
        if status in {"FAILED_REGISTRATION", "FAILED"}:
            raise RuntimeError(f"Model version not usable: {model_fqn} v{version} status={status}")

        if time.time() - t0 > timeout_seconds:
            raise TimeoutError(f"Timed out waiting for model READY: {model_fqn} v{version} status={status}")
        
        time.sleep(3)

def get_endpoint_config(endpoint_name: str) -> dict:
    host, token = get_workspace_host_and_token()
    headers = {"Authorization": f"Bearer {token}"}

    r = requests.get(f"{host}/api/2.0/serving-endpoints/{endpoint_name}/config", headers=headers, timeout=60) # try endpoint config

    if r.status_code == 404:
        r2 = requests.get(f"{host}/api/2.0/serving-endpoints/{endpoint_name}", headers=headers, timeout=60)
        r2.raise_for_status()
        data = r2.json()
        cfg = data.get("config")

        if not cfg:
            raise RuntimeError(f"Endpoint payload missing 'config' for {endpoint_name}: keys={list(data.keys())}")
        return cfg

    r.raise_for_status()

    return r.json()

def put_endpoint_config(endpoint_name: str, config: dict):
    host, token = get_workspace_host_and_token()
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"served_entities": config["served_entities"]} # send only the served_entities

    if "traffic_config" in config:
        payload["traffic_config"] = config["traffic_config"]

    # update endpoint config
    r = requests.put(
        f"{host}/api/2.0/serving-endpoints/{endpoint_name}/config",
        headers=headers,
        json=payload,
        timeout=60,
    )
    r.raise_for_status()

    return r.json()

def update_served_entity_version(config: dict, model_fqn: str, new_version: int) -> dict:
    served_entities = config.get("served_entities") or [] # read served entities list
    if not served_entities:
        raise RuntimeError("Endpoint config has no served_entities")

    matched = False
    for se in served_entities:
        if se.get("entity_name") == model_fqn: # find entity serving the model
            se["entity_version"] = str(new_version) # set the new version
            matched = True

    if not matched:
        raise RuntimeError(
            f"Did not find served entity '{model_fqn}'. Found: {[se.get('entity_name') for se in served_entities]}"
        )

    config["served_entities"] = served_entities # write back to list
    
    return config

# wait until the serving endpoint finishes applying the new config
def wait_endpoint_ready(endpoint_name: str, timeout_seconds: int = 900):
    host, token = get_workspace_host_and_token()
    headers = {"Authorization": f"Bearer {token}"}

    t0 = time.time()
    while True:
        r = requests.get(f"{host}/api/2.0/serving-endpoints/{endpoint_name}", headers=headers, timeout=60)
        r.raise_for_status()
        data = r.json()
        state = data.get("state") or {}

        ready_val = state.get("ready")
        config_update = state.get("config_update")

        ready_ok = (str(ready_val).upper() == "READY") or (ready_val is True)
        updating = str(config_update).upper() in {"IN_PROGRESS", "UPDATING"}

        if ready_ok and not updating:
            print(f"Endpoint '{endpoint_name}' is READY.")
            return

        if time.time() - t0 > timeout_seconds:
            raise TimeoutError(f"Timed out waiting for endpoint '{endpoint_name}' to become READY. state={state}")

        print(f"Waiting... ready={ready_val}, config_update={config_update}")
        time.sleep(15)

def update_endpoint_to_latest(endpoint_name: str, model_fqn: str):
    latest = get_latest_uc_model_version(model_fqn) # get newest version
    print(f"{endpoint_name}: latest version for {model_fqn} is v{latest}")
    wait_model_version_ready(model_fqn, latest, timeout_seconds=300) # wait for it to be ready

    cfg = get_endpoint_config(endpoint_name) # read current endpoint config
    cfg2 = update_served_entity_version(cfg, model_fqn, latest) # set version to latest
    put_endpoint_config(endpoint_name, cfg2) # write updated config
    print(f"Updated endpoint '{endpoint_name}' to {model_fqn} v{latest}")
    wait_endpoint_ready(endpoint_name) # wait until its updated