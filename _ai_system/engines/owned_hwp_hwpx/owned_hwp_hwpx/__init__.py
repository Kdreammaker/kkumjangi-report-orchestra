"""Owned HWP/HWPX analysis and conversion package."""

from .conversion import (
    CONVERSION_SCHEMA_VERSION,
    ENGINE_ID,
    ENGINE_VERSION,
    OwnedHwpConversionError,
    convert_hwp_to_hwpx,
)
from .corpus import build_corpus_baseline, discover_exact_pairs
from .compose_control_semantics import (
    compare_compose_control_semantics,
    model_compose_control_semantics,
    parse_hwp_compose_control_body,
    parse_hwpx_compose_root,
)
from .document_model import build_document_model_from_hwp
from .document_ir import (
    AUTHORING_HTML_CONTRACT_VERSION,
    DOCUMENT_IR_SCHEMA_VERSION,
    serializable_document_ir,
    summarize_document_ir,
    validate_document_ir,
)
from .dry_run import build_dry_run_writer_report
from .footnote_control_semantics import (
    compare_footnote_control_semantics,
    model_footnote_control_semantics,
    parse_hwp_footnote_auto_number_body,
    parse_hwp_footnote_control_body,
    parse_hwpx_footnote_root,
)
from .hwp_profile import profile_hwp_file
from .hwp_probe import probe_hwp_file
from .html_corpus import build_html_hwpx_corpus_inventory
from .html_writer import render_document_ir_to_html
from .html_reader import OwnedAuthoringHtmlError, parse_authoring_html_document_ir
from .html_hwpx_conversion import (
    convert_authoring_html_to_hwpx,
    convert_hwpx_to_authoring_html,
)
from .ir_hwpx_adapter import build_hwpx_writer_model_from_document_ir
from .hwpx_reader import OwnedHwpxReadError, read_hwpx_document_ir
from .hwpx_profile import profile_hwpx_file
from .hwpx_writer import write_dry_run_hwpx, write_hwpx_package
from .inline_control_semantics import (
    INLINE_CONTROL_CODE_TO_TAG,
    compare_inline_control_semantics,
    model_inline_control_semantics,
    parse_hwpx_inline_control_root,
)
from .line_segment_semantics import (
    LINE_SEGMENT_FIELDS,
    compare_line_segment_semantics,
    map_hwp_line_segment_text_positions,
    parse_hwp_line_segment_body,
)
from .package_validation import (
    validate_generated_hwpx,
    validate_hwpx_native_package_contract,
)
from .page_hiding_semantics import (
    compare_page_hiding_semantics,
    model_page_hiding_semantics,
    parse_hwp_page_hiding_control_body,
    parse_hwpx_page_hiding_root,
)
from .render_compatibility_semantics import (
    compare_header_compatibility_semantics,
    compare_paragraph_render_semantics,
    model_header_compatibility_semantics,
    model_paragraph_render_semantics,
    parse_hwpx_header_compatibility_root,
    parse_hwpx_paragraph_render_root,
)
from .resource_limits import (
    MAX_DECOMPRESSED_STREAM_BYTES,
    MAX_SOURCE_BYTES,
    ResourceLimitError,
    decompress_bounded,
)
from .rule_mining import build_rule_mining_report
from .text_fidelity import compare_texts, extract_hwp_text, extract_hwpx_text

__all__ = [
    "build_corpus_baseline",
    "build_document_model_from_hwp",
    "build_dry_run_writer_report",
    "build_html_hwpx_corpus_inventory",
    "build_rule_mining_report",
    "CONVERSION_SCHEMA_VERSION",
    "AUTHORING_HTML_CONTRACT_VERSION",
    "DOCUMENT_IR_SCHEMA_VERSION",
    "compare_inline_control_semantics",
    "compare_header_compatibility_semantics",
    "compare_paragraph_render_semantics",
    "compare_line_segment_semantics",
    "compare_texts",
    "convert_hwp_to_hwpx",
    "convert_authoring_html_to_hwpx",
    "convert_hwpx_to_authoring_html",
    "decompress_bounded",
    "discover_exact_pairs",
    "parse_hwp_compose_control_body",
    "parse_hwpx_compose_root",
    "parse_hwp_page_hiding_control_body",
    "parse_hwpx_page_hiding_root",
    "model_page_hiding_semantics",
    "compare_page_hiding_semantics",
    "model_compose_control_semantics",
    "compare_compose_control_semantics",
    "parse_hwp_footnote_control_body",
    "parse_hwp_footnote_auto_number_body",
    "parse_hwpx_footnote_root",
    "model_footnote_control_semantics",
    "compare_footnote_control_semantics",
    "ENGINE_ID",
    "ENGINE_VERSION",
    "MAX_DECOMPRESSED_STREAM_BYTES",
    "MAX_SOURCE_BYTES",
    "extract_hwp_text",
    "extract_hwpx_text",
    "OwnedHwpConversionError",
    "OwnedHwpxReadError",
    "OwnedAuthoringHtmlError",
    "ResourceLimitError",
    "LINE_SEGMENT_FIELDS",
    "INLINE_CONTROL_CODE_TO_TAG",
    "model_inline_control_semantics",
    "model_header_compatibility_semantics",
    "model_paragraph_render_semantics",
    "map_hwp_line_segment_text_positions",
    "parse_hwp_line_segment_body",
    "parse_hwpx_inline_control_root",
    "parse_hwpx_header_compatibility_root",
    "parse_hwpx_paragraph_render_root",
    "parse_authoring_html_document_ir",
    "profile_hwp_file",
    "probe_hwp_file",
    "profile_hwpx_file",
    "read_hwpx_document_ir",
    "build_hwpx_writer_model_from_document_ir",
    "render_document_ir_to_html",
    "serializable_document_ir",
    "summarize_document_ir",
    "validate_generated_hwpx",
    "validate_document_ir",
    "validate_hwpx_native_package_contract",
    "write_dry_run_hwpx",
    "write_hwpx_package",
]
