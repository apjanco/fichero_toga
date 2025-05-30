import logging
from pathlib import Path
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    ApiVlmOptions,
    ResponseFormat,
    InferenceFramework,
    VlmPipelineOptions,
    HuggingFaceVlmOptions
)
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.pipeline.vlm_pipeline import VlmPipeline
from docling.datamodel.base_models import FormatToExtensions

# get a list of Docling supported file extensions
supported_extensions = [a for b in FormatToExtensions.values() for a in b]

def ollama_vlm_options(model: str, prompt: str):
    options = ApiVlmOptions(
        url="http://localhost:11434/v1/chat/completions",  # the default Ollama endpoint
        params=dict(
            model=model,
        ),
        prompt=prompt,
        timeout=90,
        scale=1.0,
        response_format=ResponseFormat.MARKDOWN,
    )
    return options


def dashscope_vlm_options(model: str, prompt: str, api_key: str = None):
    # os.environ.get("DASHSCOPE_API_KEY")
    api_key = api_key
    options = ApiVlmOptions(
        url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions",
        params=dict(
            model=model,
            parameters=dict(
                max_new_tokens=400,
            ),
        ),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + api_key,
        },
        prompt=prompt,
        timeout=60,
        response_format=ResponseFormat.MARKDOWN,
    )
    return options


def sandbox_vlm_options(model: str, prompt: str, api_key: str = None):
    SANDBOX_ENDPOINT = "https://api-ai-sandbox.princeton.edu/"
    SANDBOX_API_VERSION = "2025-03-01-preview"

    api_key = api_key
    options = ApiVlmOptions(
        url=SANDBOX_ENDPOINT + "openai/deployments/" + model +
        "/chat/completions?api-version=" + SANDBOX_API_VERSION,
        params=dict(
            model=model,
            max_tokens=2000,
            temperature=0.0
        ),
        headers={
            "Content-Type": "application/json",
            "api-key": api_key,
        },
        prompt=prompt,
        timeout=60,
        response_format=ResponseFormat.MARKDOWN,
    )
    return options

def process_folders(
        app,
        models_config:list = None, 
        provider_config:dict = None
        ) -> list:
    """
    Process all files in a directory using the specified VLM type, model, and prompt.
    
    Args:
        app: The application instance containing configuration and state.
        models_config (list): A list of model configurations (not used in this function).
        provider_config (dict): A dictionary containing provider-specific configurations.
    Returns:
        list: A list of processed documents.
    """
    input_folders = app.folders
    output_folder = app.output_folder
    provider = app.model_selection.value.provider 
    model = app.model_selection.value.name 
    provider_config= provider_config[provider]
    api_key = provider_config.get('api_key', None)
    prompt = provider_config.get('prompt', "Extract text to markdown!")
    
    docs = []
    for input_dir in input_folders:
        if input_dir.is_dir():
            for file_path in input_dir.glob('**/*'):
                if file_path.suffix.lower().replace('.','') in supported_extensions:
                    print(f"Processing file 105: {file_path}")
                    doc = process_file(file_path, provider, model, prompt, api_key)
                    if doc:
                        docs.append(doc)
            return docs
        else:
            raise ValueError(f"Input path {input_dir} is not a directory.")


def process_file(input_doc_path: Path, provider: str = "dashscope", model: str = "qwen-vl-max-latest", prompt: str = "Extract text to markdown.", api_key: str = None):
    logging.basicConfig(level=logging.INFO)

    pipeline_options = VlmPipelineOptions(
        enable_remote_services=True
    )

    if provider == "ollama":
        pipeline_options.vlm_options = ollama_vlm_options(
            model=model,
            prompt=prompt,
        )

    if provider == "dashscope":
        pipeline_options.vlm_options = dashscope_vlm_options(
            model=model, prompt=prompt, api_key=api_key
        )

    if provider == "sandbox":
        pipeline_options.vlm_options = sandbox_vlm_options(
            model=model, prompt=prompt, api_key=api_key
        )

    # Create the DocumentConverter and launch the conversion.
    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options,
                pipeline_cls=VlmPipeline,
            ),
            InputFormat.IMAGE: PdfFormatOption(
                pipeline_options=pipeline_options,
                pipeline_cls=VlmPipeline,
            )
        }
    )
    return doc_converter.convert(input_doc_path)
