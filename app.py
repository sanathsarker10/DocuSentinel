import streamlit as st
from pathlib import Path
from analyzer import analyze_document
from report_generator import create_pdf_report

st.set_page_config(page_title="DocuSentinel", page_icon="🛡️", layout="wide")

st.title("🛡️ DocuSentinel")
st.subheader("Document Tampering and Authenticity Analyzer")
st.warning(
    "Prototype for screening suspicious indicators only. It cannot prove that a document is genuine "
    "or forged. Findings require human review and, where possible, verification with the issuing authority."
)

with st.sidebar:
    st.header("About this prototype")
    st.write("Upload one PDF, PNG, or JPG file. The app extracts text, inspects metadata, and runs basic image checks.")
    st.caption("Do not upload real identity documents or sensitive personal data to a public demo.")

uploaded = st.file_uploader(
    "Upload a document",
    type=["pdf", "png", "jpg", "jpeg"],
    help="For best results, use a clear scan or image. Maximum size: 10 MB."
)

if uploaded:
    if uploaded.size > 10 * 1024 * 1024:
        st.error("File exceeds the 10 MB limit. Please upload a smaller file.")
        st.stop()

    raw = uploaded.getvalue()
    with st.expander("Uploaded file details", expanded=True):
        st.write(f"**Filename:** {Path(uploaded.name).name}")
        st.write(f"**Size:** {uploaded.size / 1024:.1f} KB")
        if uploaded.type.startswith("image/"):
            st.image(raw, caption="Uploaded image", use_container_width=True)

    if st.button("Analyze document", type="primary"):
        with st.spinner("Analyzing document. This may take a few seconds..."):
            try:
                result = analyze_document(uploaded.name, raw)
                st.session_state["analysis_result"] = result
                st.session_state["analysis_filename"] = uploaded.name
            except Exception as exc:
                st.error(f"Analysis failed: {exc}")
                st.info("Check the README setup instructions and ensure Tesseract OCR is installed.")
                st.stop()

if "analysis_result" in st.session_state:
    result = st.session_state["analysis_result"]
    st.divider()
    st.header("Analysis results")

    c1, c2, c3 = st.columns(3)
    c1.metric("Findings", len(result["findings"]))
    c2.metric("Extracted characters", len(result["extracted_text"]))
    c3.metric("Pages analyzed", result["pages_analyzed"])

    st.subheader("Review status")
    st.info(result["overall_status"])
    st.caption("This status is a triage suggestion, not a probability that the document is fraudulent.")

    st.subheader("Findings")
    if result["findings"]:
        for idx, finding in enumerate(result["findings"], start=1):
            with st.expander(f"{idx}. {finding['title']} — {finding['severity']}"):
                st.write(finding["details"])
                st.caption(f"Recommended action: {finding['recommendation']}")
    else:
        st.success("No issues were flagged by the basic checks. This does not establish authenticity.")

    st.subheader("Extracted text")
    if result["extracted_text"].strip():
        st.text_area("OCR output", result["extracted_text"], height=240)
    else:
        st.warning("No text was extracted. The document may be low quality or require additional OCR language support.")

    st.subheader("Technical metadata")
    st.json(result["metadata"])

    if result.get("ela_image") is not None:
        st.subheader("ELA visualization (supporting indicator only)")
        st.image(result["ela_image"], caption="Error Level Analysis visualization. Interpretation is not definitive.", use_container_width=True)

    report_bytes = create_pdf_report(st.session_state["analysis_filename"], result)
    st.download_button(
        "Download analysis report (PDF)",
        data=report_bytes,
        file_name="docusentinel_report.pdf",
        mime="application/pdf"
    )

    st.caption("Privacy note: this prototype processes the uploaded file in the app session and does not intentionally save it to a database. Hosting providers may have their own operational logs and retention policies.")
