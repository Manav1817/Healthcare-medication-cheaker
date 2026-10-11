import joblib
import pandas as pd
import streamlit as st
from knowledge import DRUGS, ALLERGY_OPTIONS, check_safety, build_features

st.set_page_config(page_title="Medicine Safety Checker", page_icon="💊", layout="wide")


@st.cache_resource
def load_model():
    return joblib.load("model.pkl")


bundle = load_model()
model, columns = bundle["model"], bundle["columns"]

st.title("💊 Medicine Safety Checker")
st.caption("Checks whether a prescribed medicine is suitable for a patient based on allergies, "
           "previous medicines and health conditions.")

tab1, tab2 = st.tabs(["🔍 Check prescription", "ℹ️ About"])

with tab1:
    with st.sidebar:
        st.header("Patient details")
        name = st.text_input("Patient name (optional)")
        age = st.number_input("Age (years)", 0, 110, 35)
        gender = st.selectbox("Gender", ["Male", "Female"])
        pregnant = st.checkbox("Pregnant", disabled=(gender != "Female"))
        kidney = st.checkbox("Kidney disease")
        liver = st.checkbox("Liver disease")
        allergies = st.multiselect("Known allergies (drug class)", ALLERGY_OPTIONS)
        prev = st.multiselect("Previous / current medicines", sorted(DRUGS))

    st.subheader("Doctor's prescription")
    rx = st.selectbox("Prescribed medicine", sorted(DRUGS))

    if st.button("Check safety", type="primary"):
        patient = dict(age=int(age), gender=gender, pregnant=int(pregnant and gender == "Female"),
                       kidney_disease=int(kidney), liver_disease=int(liver),
                       allergies=allergies, current_meds=prev)
        feats = pd.DataFrame([build_features(patient, rx)])[columns]
        p_safe = float(model.predict_proba(feats)[0][1])
        reasons = check_safety(patient, rx)

        who = f" for {name}" if name else ""
        if reasons:
            st.error(f"❌ {rx} is NOT recommended{who}")
        elif p_safe >= 0.5:
            st.success(f"✅ {rx} appears SAFE{who}")
        else:
            st.warning(f"⚠️ {rx}{who}: model is unsure, please review manually")

        c1, c2 = st.columns(2)
        c1.metric("ML probability of being safe", f"{p_safe*100:.1f}%")
        c2.metric("Rule checks failed", len(reasons))
        st.progress(p_safe)

        if reasons:
            st.subheader("Reasons")
            for r in reasons:
                st.write("• " + r)
        else:
            st.info("No allergy, interaction or condition conflicts found in the knowledge base.")

        st.caption("⚠️ Educational demo only. Always confirm with a doctor or pharmacist.")

with tab2:
    st.markdown("""
**How it works**
1. Patient details, allergies and medicine history are converted into features.
2. A Random Forest model trained on a synthetic dataset predicts the chance the prescription is safe.
3. A rule engine checks allergies (including cross-reactivity), drug interactions, pregnancy, kidney/liver disease and age limits, and explains the result.

**Disclaimer:** synthetic data and simplified rules. Not for real clinical use.
""")
    try:
        st.dataframe(pd.read_csv("medicine_dataset.csv").head(50), use_container_width=True)
    except Exception:
        pass
