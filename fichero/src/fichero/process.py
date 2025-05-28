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


def dashscope_vlm_options(model: str, prompt: str):
    # os.environ.get("DASHSCOPE_API_KEY")
    api_key = userdata.get('DASHSCOPE_API_KEY')
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


def sandbox_vlm_options(model: str, prompt: str):
    SANDBOX_ENDPOINT = "https://api-ai-sandbox.princeton.edu/"
    SANDBOX_API_VERSION = "2025-03-01-preview"

    api_key = userdata.get('AI_SANDBOX_KEY')
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


def process_directory(input_dir_path: Path, type: str = "dashscope", model: str = "qwen-vl-max-latest", prompt: str = "Extract text to markdown."):
    if input_dir_path.is_dir():
        docs = []
        for file_path in input_dir_path.glob('**/*'):
            if file_path.suffix.lower() in supported_extensions:
                doc = process_file(file_path, type, model, prompt)
                if doc:
                    docs.append(doc)
        return docs
    else:
        raise ValueError(f"Input path {input_dir_path} is not a directory.")


def process_file(input_doc_path: Path, type: str = "dashscope", model: str = "qwen-vl-max-latest", prompt: str = "Extract text to markdown."):
    logging.basicConfig(level=logging.INFO)

    pipeline_options = VlmPipelineOptions(
        enable_remote_services=True
    )

    if type == "ollama":
        pipeline_options.vlm_options = ollama_vlm_options(
            model=model,
            prompt=prompt,
        )

    if type == "dashscope":
        pipeline_options.vlm_options = dashscope_vlm_options(
            model=model, prompt=prompt
        )

    if type == "sandbox":
        pipeline_options.vlm_options = sandbox_vlm_options(
            model=model, prompt=prompt
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
