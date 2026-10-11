import random
import pandas as pd

# cls = drug class, preg = unsafe in pregnancy, kidney/liver = unsafe with that disease, min_age = minimum age (years)
DRUGS = {
    "Amoxicillin":   dict(cls="penicillin",    preg=0, kidney=0, liver=0, min_age=0),
    "Ampicillin":    dict(cls="penicillin",    preg=0, kidney=0, liver=0, min_age=0),
    "Cephalexin":    dict(cls="cephalosporin", preg=0, kidney=0, liver=0, min_age=0),
    "Azithromycin":  dict(cls="macrolide",     preg=0, kidney=0, liver=1, min_age=0),
    "Ciprofloxacin": dict(cls="fluoroquinolone", preg=1, kidney=0, liver=0, min_age=18),
    "Doxycycline":   dict(cls="tetracycline",  preg=1, kidney=0, liver=0, min_age=8),
    "Cotrimoxazole": dict(cls="sulfa",         preg=1, kidney=1, liver=0, min_age=0),
    "Ibuprofen":     dict(cls="nsaid",         preg=1, kidney=1, liver=0, min_age=1),
    "Diclofenac":    dict(cls="nsaid",         preg=1, kidney=1, liver=1, min_age=12),
    "Naproxen":      dict(cls="nsaid",         preg=1, kidney=1, liver=0, min_age=12),
    "Aspirin":       dict(cls="aspirin",       preg=1, kidney=1, liver=0, min_age=16),
    "Paracetamol":   dict(cls="analgesic",     preg=0, kidney=0, liver=1, min_age=0),
    "Tramadol":      dict(cls="opioid",        preg=1, kidney=1, liver=1, min_age=12),
    "Codeine":       dict(cls="opioid",        preg=1, kidney=0, liver=0, min_age=12),
    "Warfarin":      dict(cls="anticoagulant", preg=1, kidney=0, liver=1, min_age=18),
    "Metformin":     dict(cls="antidiabetic",  preg=0, kidney=1, liver=0, min_age=10),
    "Atorvastatin":  dict(cls="statin",        preg=1, kidney=0, liver=1, min_age=10),
    "Lisinopril":    dict(cls="ace_inhibitor", preg=1, kidney=1, liver=0, min_age=6),
    "Losartan":      dict(cls="arb",           preg=1, kidney=1, liver=0, min_age=6),
    "Amlodipine":    dict(cls="ccb",           preg=0, kidney=0, liver=0, min_age=6),
    "Omeprazole":    dict(cls="ppi",           preg=0, kidney=0, liver=0, min_age=1),
    "Cetirizine":    dict(cls="antihistamine", preg=0, kidney=0, liver=0, min_age=2),
    "Sertraline":    dict(cls="ssri",          preg=0, kidney=0, liver=0, min_age=6),
    "Salbutamol":    dict(cls="bronchodilator", preg=0, kidney=0, liver=0, min_age=0),
}

CLASSES = sorted(set(d["cls"] for d in DRUGS.values()))
ALLERGY_OPTIONS = ["penicillin", "cephalosporin", "sulfa", "nsaid", "aspirin", "opioid",
                   "macrolide", "fluoroquinolone", "tetracycline", "statin", "ace_inhibitor"]

# allergy -> drug classes that are blocked (includes cross-reactivity)
CROSS = {
    "penicillin": ["penicillin", "cephalosporin"],
    "aspirin": ["aspirin", "nsaid"],
    "nsaid": ["nsaid", "aspirin"],
}

# (prescribed class, class patient already takes, reason)
INTERACTIONS = {
    ("nsaid", "anticoagulant"): "NSAID + anticoagulant raises bleeding risk",
    ("aspirin", "anticoagulant"): "Aspirin + anticoagulant raises bleeding risk",
    ("anticoagulant", "nsaid"): "Anticoagulant + NSAID raises bleeding risk",
    ("anticoagulant", "aspirin"): "Anticoagulant + aspirin raises bleeding risk",
    ("nsaid", "nsaid"): "Duplicate NSAID therapy",
    ("nsaid", "aspirin"): "NSAID + aspirin duplicate therapy / GI bleeding",
    ("aspirin", "nsaid"): "Aspirin + NSAID duplicate therapy / GI bleeding",
    ("nsaid", "ace_inhibitor"): "NSAID + ACE inhibitor can harm kidneys",
    ("nsaid", "arb"): "NSAID + ARB can harm kidneys",
    ("ace_inhibitor", "nsaid"): "ACE inhibitor + NSAID can harm kidneys",
    ("arb", "nsaid"): "ARB + NSAID can harm kidneys",
    ("ace_inhibitor", "arb"): "ACE inhibitor + ARB dual blockade",
    ("arb", "ace_inhibitor"): "ARB + ACE inhibitor dual blockade",
    ("opioid", "ssri"): "Opioid + SSRI risk of serotonin syndrome",
    ("ssri", "opioid"): "SSRI + opioid risk of serotonin syndrome",
    ("opioid", "opioid"): "Duplicate opioid therapy",
    ("ssri", "nsaid"): "SSRI + NSAID raises bleeding risk",
    ("nsaid", "ssri"): "NSAID + SSRI raises bleeding risk",
    ("ssri", "aspirin"): "SSRI + aspirin raises bleeding risk",
    ("aspirin", "ssri"): "Aspirin + SSRI raises bleeding risk",
    ("fluoroquinolone", "antidiabetic"): "Fluoroquinolone + antidiabetic can cause blood sugar swings",
    ("sulfa", "anticoagulant"): "Sulfa antibiotic increases anticoagulant effect",
    ("sulfa", "antidiabetic"): "Sulfa antibiotic can cause hypoglycemia with antidiabetics",
    ("macrolide", "statin"): "Macrolide + statin raises muscle toxicity risk",
    ("macrolide", "anticoagulant"): "Macrolide increases anticoagulant effect",
}


def allergy_hit(allergies, drug_cls):
    for a in allergies:
        if drug_cls in CROSS.get(a, [a]):
            return a
    return None


def check_safety(p, drug):
    # Returns a list of reasons the drug is unsafe (empty list = no problem found)
    d = DRUGS[drug]
    reasons = []
    hit = allergy_hit(p["allergies"], d["cls"])
    if hit:
        reasons.append(f"Allergy conflict: patient is allergic to {hit} (drug class: {d['cls']})")
    for m in p["current_meds"]:
        if m in DRUGS:
            msg = INTERACTIONS.get((d["cls"], DRUGS[m]["cls"]))
            if msg:
                reasons.append(f"Interaction with {m}: {msg}")
    if p["pregnant"] and d["preg"]:
        reasons.append("Unsafe during pregnancy")
    if p["kidney_disease"] and d["kidney"]:
        reasons.append("Unsafe with kidney disease")
    if p["liver_disease"] and d["liver"]:
        reasons.append("Unsafe with liver disease")
    if p["age"] < d["min_age"]:
        reasons.append(f"Below minimum age ({d['min_age']} yrs)")
    return reasons


def build_features(p, drug):
    d = DRUGS[drug]
    f = {
        "age": p["age"],
        "is_female": int(p["gender"] == "Female"),
        "pregnant": int(p["pregnant"]),
        "kidney_disease": int(p["kidney_disease"]),
        "liver_disease": int(p["liver_disease"]),
        "n_allergies": len(p["allergies"]),
        "n_current_meds": len(p["current_meds"]),
    }
    for a in ALLERGY_OPTIONS:
        f["allergy_" + a] = int(a in p["allergies"])
    cur = [DRUGS[m]["cls"] for m in p["current_meds"] if m in DRUGS]
    for c in CLASSES:
        f["on_" + c] = cur.count(c)
    for n in DRUGS:
        f["rx_" + n] = int(n == drug)
    f["allergy_conflict"] = int(allergy_hit(p["allergies"], d["cls"]) is not None)
    f["interaction_count"] = sum(1 for c in cur if (d["cls"], c) in INTERACTIONS)
    f["age_below_min"] = int(p["age"] < d["min_age"])
    f["preg_risk"] = int(p["pregnant"] and d["preg"])
    f["kidney_risk"] = int(p["kidney_disease"] and d["kidney"])
    f["liver_risk"] = int(p["liver_disease"] and d["liver"])
    return f


def row_to_patient(row):
    split = lambda s: [x for x in str(s).split(";") if x and x != "nan"]
    return dict(age=int(row["age"]), gender=row["gender"], pregnant=int(row["pregnant"]),
                kidney_disease=int(row["kidney_disease"]), liver_disease=int(row["liver_disease"]),
                allergies=split(row["allergies"]), current_meds=split(row["previous_medicines"]))


def generate_dataset(n=6000, seed=42):
    rnd = random.Random(seed)
    rows = []
    drug_names = list(DRUGS)
    for i in range(n):
        age = int(min(95, max(1, rnd.gauss(42, 22))))
        gender = rnd.choice(["Male", "Female"])
        pregnant = int(gender == "Female" and 16 <= age <= 45 and rnd.random() < 0.10)
        kidney = int(rnd.random() < (0.05 if age < 50 else 0.15))
        liver = int(rnd.random() < 0.07)
        allergies = [a for a in ALLERGY_OPTIONS if rnd.random() < 0.06]
        k = rnd.choices([0, 1, 2, 3, 4], weights=[25, 30, 25, 15, 5])[0]
        meds = rnd.sample(drug_names, k)
        drug = rnd.choice(drug_names)
        p = dict(age=age, gender=gender, pregnant=pregnant, kidney_disease=kidney,
                 liver_disease=liver, allergies=allergies, current_meds=meds)
        reasons = check_safety(p, drug)
        rows.append(dict(patient_id=f"P{i+1:05d}", age=age, gender=gender, pregnant=pregnant,
                         kidney_disease=kidney, liver_disease=liver,
                         allergies=";".join(allergies), previous_medicines=";".join(meds),
                         prescribed_medicine=drug, is_safe=int(len(reasons) == 0),
                         reason=" | ".join(reasons) if reasons else "No issues found"))
    return pd.DataFrame(rows)
