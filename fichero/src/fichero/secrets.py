import toga
import srsly

def get_models_config(app:toga.App) -> dict:
    """
    Returns the configuration for the models.
    """
    # check if the models_config.json file exists
    #https://toga.readthedocs.io/en/stable/reference/api/resources/app_paths.html#toga.paths.Paths.data
    config_data_path = (app.paths.data / "models_config.jsonl") 
    if not config_data_path.exists():
        # If it does not exist, create a default configuration
        models_config = list(srsly.read_jsonl(app.paths.app / "resources"/ "models_config.start.jsonl"))
        # if directory does not exist, create it
        if not app.paths.data.exists():
            app.paths.data.mkdir(parents=True, exist_ok=True)   
        # Save the default configuration to the file
        srsly.write_jsonl(app.paths.data / "models_config.jsonl", models_config)
    return list(srsly.read_jsonl(app.paths.data / "models_config.jsonl"))

