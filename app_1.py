import os
import math
import pandas as pd
import streamlit as st
from supabase import create_client, Client
from datetime import date
import altair as alt

def key_factory(prefix: str, project_id: str):
    return lambda label: f"{prefix}:{project_id}:{label}"

def render_new_project_form():
    with st.form("new_project_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            np_navn  = st.text_input("ProjektNavn *")
            np_akr   = st.text_input("Projektakronym")
            np_pool  = st.number_input("Pool (numeric)", min_value=0.0, step=1.0, format="%.0f")
            np_ws    = st.number_input("Workstream (numeric)", min_value=0, step=1)
            np_start = st.date_input("Start", value=date.today())
            np_slut  = st.date_input("Slut")
        with c2:
            np_leder  = st.text_input("Projektleder")
            np_varig  = st.text_input("Varighed", placeholder="ex. 3 years and 2 months")
            np_form   = st.text_area("Formål/Beskrivelse")
            np_budget = st.number_input("Budget (numeric)", min_value=0.0, step=1000.0, format="%.0f")
        create_ok = st.form_submit_button("Create project")

    fields = {
        "np_navn": np_navn, "np_akr": np_akr, "np_pool": np_pool, "np_ws": np_ws,
        "np_start": np_start, "np_slut": np_slut, "np_leder": np_leder,
        "np_varig": np_varig, "np_form": np_form, "np_budget": np_budget,
    }
    return create_ok, fields

def render_ws1_tracking_form(selected_project_id: str):
    def _none_if(cond, val):
        return (val if cond else None)

    k = key_factory("ws1", selected_project_id)

    with st.form(f"ws1_tracking_form:{selected_project_id}", clear_on_submit=True):
        st.markdown("<h1 style='text-align: center;'>Workstream 1 - Chemical CO2 Capture</h1>", unsafe_allow_html=True)
        st.markdown("### Project status and progression")

        status = st.selectbox("What is the current status of the project?",
        [
        "Green - Project is progressing according to current project plan",
        "Yellow - Project is mostly progressing according to current project plan with minor changes or delays",
        "Red - Changes and delays cause the project to diverge from the current project plan"
        ], key=k("status"))

        unforeseen = st.radio("Have any unforeseen challenges arisen during the project?", ["No","Yes"], horizontal=True, key=k("unforeseen"))
        challenges = st.text_area("If yes, what challenges?", help="Only fill this if you selected 'Yes' above.", key=k("challenges"))

        res_constr = st.radio("Are there any resource constraints affecting the progress of the project?", ["No","Yes"], horizontal=True, key=k("res_constr"))
        constraints_sel = st.multiselect("If Yes, which constraints?", ["Personnel","Funding","Equipment"], help="Only select if you answered 'Yes' above.", key=k("constraints_sel"))
        constraints_other = st.text_input("Other constraints", help="Only fill if 'Yes' above.", key=k("constraints_other"))

        st.markdown("### The project's technology development")
        tech_types = st.multiselect(
            "What type(s) of method/technology is the project developing/testing?",
            [
                "Post-combustion capture (e.g., amine-based, carbonates, adsorption, membranes)",
                "Pre-combustion capture (e.g., via gasification and separation)",
                "Oxy-fuel combustion (combustion in pure oxygen)",
                "Direct air capture",
                "Bioenergy with CO₂ capture (BECCS)",
                "Industrial CO₂ capture (e.g., from cement, steel, and chemical production)",
            ],
            key=k("tech_types")
        )
        tech_other = st.text_input("Other type of technology (optional)", key=k("tech_other"))
        tech_descr = st.text_area("Briefly describe the technology being developed/tested", key=k("tech_descr"))

        st.markdown("### Technological maturity (TRL - Technology Readiness Level)")
        trl_start   = st.number_input("TRL at project start", min_value=1, max_value=9, step=1, key=k("trl_start"))
        trl_current = st.number_input("TRL currently",       min_value=1, max_value=9, step=1, key=k("trl_current"))
        trl_increase_reason = st.text_area("What has caused the increase in TRL level?", help="Only fill if TRL increased.", key=k("trl_increase_reason"))

        st.markdown("### Contribution to overall goals")
        extent_opts = ["To a great extent","To some extent","To a lesser extent","To a small extent","Not at all"]
        contrib_project = st.radio(
            'Has the project itself contributed to getting closer to this long term inflection point?\n'
            '“Cost-effective CO₂ capture enables market-driven implementation” Achieving this inflection point '
            'will require cost reductions through innovation, supportive policies, clear regulations, robust infrastructure, and societal engagement.',
            extent_opts,
            key=k("contrib_project")
        )
        contrib_project_how = st.text_area("How/why? (please describe)", key=k("contrib_project_how"))

        contrib_society = st.radio("Has the technological/market development in society got nearer the inflection point?", extent_opts, key=k("contrib_society"))
        contrib_society_how = st.text_area("How/Why? What are the main challenges to get nearer to the inflection point?", key=k("contrib_society_how"))

        st.markdown("### Project indicators")
        st.markdown("##### Energy efficiency")
        energy_opts = ["Yes","No","Indeterminate/Unknown","Not relevant question to the project"]
        energy_gj  = st.number_input("Energy required per 1 ton CO₂ (GJ/ton)", min_value=0.0, step=0.5, key=k("energy_gj"))
        energy_kwh = st.number_input("Alternatively: kWh/ton CO₂", min_value=0.0, step=1.0, key=k("energy_kwh"))
        energy_improved = st.radio("Has there been an increase in the energy efficiency of the tested technology since project start?", energy_opts, horizontal=True, key=k("energy_improved"))
        energy_from = st.number_input("Energy efficiency at project start (%)", min_value=0.0, max_value=100.0, step=0.5, help="Only relevant if 'Yes' above.", key=k("energy_from"))
        energy_to   = st.number_input("Energy efficiency now (%)",   min_value=0.0, max_value=100.0, step=0.1, help="Only relevant if 'Yes' above.", key=k("energy_to"))

        st.markdown("##### Capture efficiency")
        capture_opts = ["Yes","No","Indeterminate/Unknown","Not relevant question to the project"]
        cap_pct = st.number_input("Approximately what percentage of the CO₂ can the project’s tested technology capture?", min_value=0.0, max_value=100.0, step=0.5, key=k("cap_pct"))
        cap_improved = st.radio("Has there been an increase in the technology’s capture efficiency since the start of the project?", capture_opts, horizontal=True, key=k("cap_improved"))
        cap_from = st.number_input("Capture efficiency at project start (%)", min_value=0.0, max_value=100.0, step=0.5, help="Only relevant if 'Yes' above.", key=k("cap_from"))
        cap_to   = st.number_input("Capture efficiency now (%)",     min_value=0.0, max_value=100.0, step=0.5, help="Only relevant if 'Yes' above.", key=k("cap_to"))

        st.markdown("##### Gas purity")
        purity_pct = st.number_input("What is achieved gas purity of the captured CO₂ in the project? (%)", min_value=0.0, max_value=100.0, step=0.1, key=k("purity_pct"))
        purity_improved = st.radio("Has the project achieved an increase in the gas purity of the captured CO₂ since project start?", energy_opts, horizontal=True, key=k("purity_improved"))
        purity_from = st.number_input("Gas purity at project start (%)", min_value=0.0, max_value=100.0, step=0.5, help="Only relevant if 'Yes' above.", key=k("purity_from"))
        purity_to   = st.number_input("Gas purity now (%)",     min_value=0.0, max_value=100.0, step=0.5, help="Only relevant if 'Yes' above.", key=k("purity_to"))

        gas_monitoring = st.radio("Has the project improved monitoring and controlling gas impurities?", energy_opts, horizontal=True, key=k("gas_monitoring"))
        gas_monitoring_how = st.text_area("How? (Describe improvements in monitoring/controlling gas impurities)", key=k("gas_monitoring_how"))

        st.markdown("##### Corrosivity and material durability")
        corrosivity = st.checkbox("Corrosivity addressed?", key=k("corrosivity"))
        solvent_deg = st.checkbox("Solvent degradation addressed?", key=k("solvent_deg"))
        material_dur = st.checkbox("Material durability addressed?", key=k("material_dur"))
        toxic_emiss = st.checkbox("Emission of toxic byproducts during operation addressed?", key=k("toxic_emiss"))
        corrosivity_how = st.text_area("How have these challenges been addressed? (Or mark 'Not relevant question to the project')", key=k("corrosivity_how"))

        st.markdown("##### Economic efficiency")
        cost_opts = ["Yes","No","Indeterminate/Unknown","Not relevant question to the project"]
        cost_dkk = st.number_input("What costs are required to capture 1 ton of CO₂ with the project’s tested technology? (DKK)", min_value=0.0, step=1.0, key=k("cost_dkk"))
        cost_improved = st.radio("Have improvements in cost efficiency been achieved in the project?", cost_opts, horizontal=True, key=k("cost_improved"))
        cost_impr_pct = st.number_input("If yes, approximately how much improvement (%)", min_value=0.0, max_value=100.0, step=0.5, help="Only relevant if 'Yes' above.", key=k("cost_impr_pct"))

        st.markdown("##### Scaling potential")
        scalable = st.radio("Is the tested technology scalable to capture CO₂ in megaton quantities?", ["Yes","No","Indeterminate/Unknown"], horizontal=True, key=k("scalable"))
        scale_barriers = st.text_area("What barriers/challenges are to be overcome before the technology can be upscaled to capture CO₂ in megaton?", key=k("scale_barriers"))

        st.markdown("### Final reflections")
        gap_opts = ["Yes","No","Indeterminate/Unknown"]
        knowledge_gaps = st.radio("Has your project identified any specific knowledge gaps, limitations, or challenges encountered during its implementation that should be addressed in future INNO-CCUS projects or initiatives?", gap_opts, horizontal=True, key=k("knowledge_gaps"))
        knowledge_gaps_descr = st.text_area("If yes, please describe them and suggest potential approaches or areas for further investigation.", key=k("knowledge_gaps_descr"))

        add = st.form_submit_button("Add tracking entry", key=k("submit"))

    payload = {
        "project_id": selected_project_id,
        "status": status,
        "unforeseen_challenges": (unforeseen == "Yes"),
        "challenges": _none_if(unforeseen == "Yes", (challenges.strip() or None)),
        "resource_constraints": (res_constr == "Yes"),
        "constraints_selected": _none_if(res_constr == "Yes", (", ".join(constraints_sel) or None)),
        "constraints_other": _none_if(res_constr == "Yes", (constraints_other.strip() or None)),
        "tech_types": (", ".join(tech_types) or None),
        "tech_other": (tech_other.strip() or None),
        "tech_description": (tech_descr.strip() or None),
        "trl_start": int(trl_start),
        "trl_current": int(trl_current),
        "trl_increase_reason": _none_if(trl_current > trl_start, (trl_increase_reason.strip() or None)),
        "contrib_project": contrib_project,
        "contrib_project_how": (contrib_project_how.strip() or None),
        "contrib_society": contrib_society,
        "contrib_society_how": (contrib_society_how.strip() or None),
        "energy_gj_per_ton": float(energy_gj),
        "energy_kwh_per_ton": float(energy_kwh),
        "energy_eff_improved": energy_improved,
        "energy_eff_from_pct": _none_if(energy_improved == "Yes", float(energy_from)),
        "energy_eff_to_pct": _none_if(energy_improved == "Yes", float(energy_to)),
        "capture_pct": float(cap_pct),
        "capture_improved": cap_improved,
        "capture_from_pct": _none_if(cap_improved == "Yes", float(cap_from)),
        "capture_to_pct": _none_if(cap_improved == "Yes", float(cap_to)),
        "purity_pct": float(purity_pct),
        "purity_improved": purity_improved,
        "purity_from_pct": _none_if(purity_improved == "Yes", float(purity_from)),
        "purity_to_pct": _none_if(purity_improved == "Yes", float(purity_to)),
        "gas_monitoring": gas_monitoring,
        "gas_monitoring_how": (gas_monitoring_how.strip() or None),
        "corrosivity": corrosivity,
        "solvent_deg": solvent_deg,
        "material_dur": material_dur,
        "toxic_emiss": toxic_emiss,
        "corrosivity_how": (corrosivity_how.strip() or None),
        "cost_dkk_per_ton": float(cost_dkk),
        "cost_improved": cost_improved,
        "cost_improvement_pct": _none_if(cost_improved == "Yes", float(cost_impr_pct)),
        "scalable_megaton": scalable,
        "scale_barriers": (scale_barriers.strip() or None),
        "knowledge_gaps": knowledge_gaps,
        "knowledge_gaps_descr": (knowledge_gaps_descr.strip() or None),
    }
    return add, payload

def render_ws2_tracking_form(selected_project_id: str):
    def _none_if(cond, val):
        return (val if cond else None)

    k = key_factory("ws2", selected_project_id)

    with st.form(f"ws2_tracking_form:{selected_project_id}", clear_on_submit=True):
        st.markdown("<h1 style='text-align: center;'>Workstream 2 - Biological CO2 Capture and Storage</h1>", unsafe_allow_html=True)
        st.markdown("### Project status and progression")

        status = st.selectbox("What is the current status of the project?",
        [
        "Green - Project is progressing according to current project plan",
        "Yellow - Project is mostly progressing according to current project plan with minor changes or delays",
        "Red - Changes and delays cause the project to diverge from the current project plan"
        ], key=k("status"))

        unforeseen = st.radio("Have any unforeseen challenges arisen during the project?", ["No","Yes"], horizontal=True, key=k("unforeseen"))
        challenges = st.text_area("If yes, what challenges?", help="Only fill this if you selected 'Yes' above.", key=k("challenges"))

        res_constr = st.radio("Are there any resource constraints affecting the progress of the project?", ["No","Yes"], horizontal=True, key=k("res_constr"))
        constraints_sel = st.multiselect("If Yes, which constraints?", ["Personnel","Funding","Equipment"], help="Only select if you answered 'Yes' above.", key=k("constraints_sel"))
        constraints_other = st.text_input("Other constraints", help="Only fill if 'Yes' above.", key=k("constraints_other"))

        st.markdown("### The project's technology development")
        tech_types = st.multiselect(
            "What type(s) of method/technology is the project developing/testing?",
            [
                "Blue carbon enhancement in marine and coastal ecosystems",
                "Biochar production and soil application",
                "Assessment and optimization of biochar stability for permanence",
                "Integration of biochar in building materials",
                "Innovative and multifunctional afforestation/forestry",
                "Monitoring, reporting, and verification (MRV) tools for biological carbon storage",
            ],
            key=k("tech_types")
        )
        tech_other = st.text_input("Other type of technology (optional)", key=k("tech_other"))
        tech_descr = st.text_area("Briefly describe the technology being developed/tested", key=k("tech_descr"))

        st.markdown("### Technological maturity (TRL - Technology Readiness Level)")
        trl_start   = st.number_input("TRL at project start", min_value=1, max_value=9, step=1, key=k("trl_start"))
        trl_current = st.number_input("TRL currently",       min_value=1, max_value=9, step=1, key=k("trl_current"))
        trl_increase_reason = st.text_area("What has caused the increase in TRL level?", help="Only fill if TRL increased.", key=k("trl_increase_reason"))

        st.markdown("### Contribution to overall goals")
        extent_opts = ["To a great extent","To some extent","To a lesser extent","To a small extent","Not at all"]
        contrib_project = st.radio(
            'Has the project itself contributed to getting closer to this long term inflection point?\n'
            'Systemic integration of nature-based solutions in Denmark’s carbon management, by 2040.',
            extent_opts,
            key=k("contrib_project")
        )
        contrib_project_how = st.text_area("How/why? (please describe)", key=k("contrib_project_how"))

        contrib_society = st.radio("Has the technological/market development in society got nearer the inflection point?", extent_opts, key=k("contrib_society"))
        contrib_society_how = st.text_area("How/Why? What are the main challenges to get nearer to the inflection point?", key=k("contrib_society_how"))

        st.markdown("### Project indicators")
        st.markdown("##### Development of monitoring and standardization tools")
        mrv_opts = ["Yes","No","Indeterminate/Unknown","Not relevant to the project"]
        mrv_contrib = st.radio("Has the project contributed to development of MRV protocols for carbon flows and storage permanence?", mrv_opts, horizontal=True, key=k("mrv_contrib"))
        mrv_validated = st.radio("If yes, have the protocols been independently validated or adopted by third parties?", ["Yes","No","Indeterminate/Unknown","Not relevant to the project"], horizontal=True, key=k("mrv_validated"))
        mrv_method = st.multiselect(
            "What type of method does your project’s MRV protocol use to track carbon flows and storage permanence?",
            [
                "Direct measurement (e.g., field sampling, gas flux sensors, biomass inventories)",
                "Remote sensing (e.g., satellite imagery, drones, aerial surveys)",
                "Modeling or estimation (e.g., process-based models, default factors, simulation software)",
                "Hybrid approach (combining two or more of the above)",
            ],
            key=k("mrv_method")
        )
        mrv_other = st.text_input("Other MRV method (optional)", key=k("mrv_other"))
        mrv_not_relevant = st.checkbox("Not relevant to the project (MRV)", key=k("mrv_not_relevant"))

        st.markdown("##### Site mapping and selection")
        site_opts = ["Yes","No","Indeterminate/Unknown","Not relevant to the project"]
        site_mapping = st.radio("Has the project improved mapping, selection of intervention sites for carbon capture/storage?", site_opts, horizontal=True, key=k("site_mapping"))
        site_methods = st.text_area("If yes, what methods and data have been used in that process?", key=k("site_methods"))

        st.markdown("##### Long-Term Storage Permanence")
        perm_opts = ["Yes","No","Indeterminate/Unknown","Not relevant to the project"]
        perm_achieved = st.radio("Has the tested technology in the project achieved permanence of the carbon biologically stored?", perm_opts, horizontal=True, key=k("perm_achieved"))
        perm_pct = st.number_input("What percentage of the initially stored CO₂ is expected to remain stored after 100 years?", min_value=0.0, max_value=100.0, step=0.1, key=k("perm_pct"))
        perm_how = st.text_area("How does the project ensure the permanence and long-term stability of the sequestered carbon?", key=k("perm_how"))

        st.markdown("##### Biosystem impacts")
        impact_biodiversity = st.checkbox("Biodiversity", key=k("impact_biodiversity"))
        impact_water_quality = st.checkbox("Water quality", key=k("impact_water_quality"))
        impact_climate_resilience = st.checkbox("Local climate resilience / flood regulation", key=k("impact_climate_resilience"))
        impact_soil_health = st.checkbox("Soil formation and soil health/fertility", key=k("impact_soil_health"))
        impact_nutrient_cycling = st.checkbox("Nutrient cycling (e.g., nitrogen and phosphorus)", key=k("impact_nutrient_cycling"))
        impact_raw_materials = st.checkbox("Provision of raw materials (such as timber, reeds etc.)", key=k("impact_raw_materials"))
        impact_other = st.text_area("Other positive impacts?", key=k("impact_other"))

        st.markdown("##### Process efficiency")
        proc_opts = ["Yes","No","Indeterminate/Unknown","Not relevant to the project"]
        proc_eff = st.radio("Has the project improved process efficiency of the tested technology for biological CO₂ capture and storage?", proc_opts, horizontal=True, key=k("proc_eff"))
        proc_eff_how = st.text_area("If yes, how?", key=k("proc_eff_how"))

        st.markdown("##### Scaling potential")
        scale_opts = ["Yes","No","Indeterminate/Unknown","Not relevant to the project"]
        scalable = st.radio("Is the tested technology scalable to store CO₂ in million tonnes per year?", scale_opts, horizontal=True, key=k("scalable"))
        scale_barriers = st.text_area("What are the main challenges/barriers to be overcome to reach such upscaling?", key=k("scale_barriers"))
        scale_land = st.checkbox("Available land", key=k("scale_land"))
        scale_legal = st.text_input("Legal challenges", key=k("scale_legal"))
        scale_economic = st.text_input("Economic challenges", key=k("scale_economic"))
        scale_societal = st.text_input("Societal factors", key=k("scale_societal"))
        scale_other = st.text_input("Other factors", key=k("scale_other"))

        st.markdown("### Final reflections")
        gap_opts = ["Yes","No","Indeterminate/Unknown"]
        knowledge_gaps = st.radio("Has your project identified any specific knowledge gaps, limitations, or challenges encountered during its implementation that should be addressed in future INNO-CCUS projects or initiatives?", gap_opts, horizontal=True, key=k("knowledge_gaps"))
        knowledge_gaps_descr = st.text_area("If yes, please describe them and suggest potential approaches or areas for further investigation.", key=k("knowledge_gaps_descr"))

        add = st.form_submit_button("Add tracking entry", key=k("submit"))

    payload = {
        "project_id": selected_project_id,
        "status": status,
        "unforeseen_challenges": (unforeseen == "Yes"),
        "challenges": _none_if(unforeseen == "Yes", (challenges.strip() or None)),
        "resource_constraints": (res_constr == "Yes"),
        "constraints_selected": _none_if(res_constr == "Yes", (", ".join(constraints_sel) or None)),
        "constraints_other": _none_if(res_constr == "Yes", (constraints_other.strip() or None)),
        "tech_types": (", ".join(tech_types) or None),
        "tech_other": (tech_other.strip() or None),
        "tech_description": (tech_descr.strip() or None),
        "trl_start": int(trl_start),
        "trl_current": int(trl_current),
        "trl_increase_reason": _none_if(trl_current > trl_start, (trl_increase_reason.strip() or None)),
        "contrib_project": contrib_project,
        "contrib_project_how": (contrib_project_how.strip() or None),
        "contrib_society": contrib_society,
        "contrib_society_how": (contrib_society_how.strip() or None),
        "mrv_contrib": mrv_contrib,
        "mrv_validated": mrv_validated,
        "mrv_method": (", ".join(mrv_method) or None),
        "mrv_other": (mrv_other.strip() or None),
        "mrv_not_relevant": mrv_not_relevant,
        "site_mapping": site_mapping,
        "site_methods": (site_methods.strip() or None),
        "perm_achieved": perm_achieved,
        "perm_pct": float(perm_pct),
        "perm_how": (perm_how.strip() or None),
        "impact_biodiversity": impact_biodiversity,
        "impact_water_quality": impact_water_quality,
        "impact_climate_resilience": impact_climate_resilience,
        "impact_soil_health": impact_soil_health,
        "impact_nutrient_cycling": impact_nutrient_cycling,
        "impact_raw_materials": impact_raw_materials,
        "impact_other": (impact_other.strip() or None),
        "proc_eff": proc_eff,
        "proc_eff_how": (proc_eff_how.strip() or None),
        "scalable": scalable,
        "scale_barriers": (scale_barriers.strip() or None),
        "scale_land": scale_land,
        "scale_legal": (scale_legal.strip() or None),
        "scale_economic": (scale_economic.strip() or None),
        "scale_societal": (scale_societal.strip() or None),
        "scale_other": (scale_other.strip() or None),
        "knowledge_gaps": knowledge_gaps,
        "knowledge_gaps_descr": (knowledge_gaps_descr.strip() or None),
    }
    return add, payload

def render_ws3_tracking_form(selected_project_id: str):
    def _none_if(cond, val):
        return (val if cond else None)

    k = key_factory("ws3", selected_project_id)

    with st.form(f"ws3_tracking_form:{selected_project_id}", clear_on_submit=True):
        st.markdown("<h1 style='text-align: center;'>Workstream 3 - Geological CO₂ Storage</h1>", unsafe_allow_html=True)
        st.markdown("### Project status and progression")

        status = st.selectbox("What is the current status of the project?",
        [
        "Green - Project is progressing according to current project plan",
        "Yellow - Project is mostly progressing according to current project plan with minor changes or delays",
        "Red - Changes and delays cause the project to diverge from the current project plan"
        ], key=k("status"))

        unforeseen = st.radio("Have any unforeseen challenges arisen during the project?", ["No","Yes"], horizontal=True, key=k("unforeseen"))
        challenges = st.text_area("If yes, what challenges?", help="Only fill this if you selected 'Yes' above.", key=k("challenges"))

        res_constr = st.radio("Are there any resource constraints affecting the progress of the project?", ["No","Yes"], horizontal=True, key=k("res_constr"))
        constraints_sel = st.multiselect("If Yes, which constraints?", ["Personnel","Funding","Equipment"], help="Only select if you answered 'Yes' above.", key=k("constraints_sel"))
        constraints_other = st.text_input("Other constraints", help="Only fill if 'Yes' above.", key=k("constraints_other"))

        st.markdown("### The project's technology development")
        storage_types = st.multiselect(
            "What type(s) of method/technology for geological CO₂ storage is the project developing/testing?",
            [
                "Saline Aquifer Storage",
                "Depleted Oil and Gas Reservoirs",
                "Enhanced Oil Recovery (EOR)",
                "Unmineable Coal Seams (ECBM)",
                "Basaltic Rock Storage (Mineralization)",
            ],
            key=k("storage_types")
        )
        injection_monitoring = st.multiselect(
            "What type(s) of technologies for injection and monitoring?",
            [
                "Well Drilling",
                "Caprock Integrity Testing",
                "Monitoring, Reporting, and Verification (MRV)",
            ],
            key=k("injection_monitoring")
        )
        tech_descr = st.text_area("Briefly describe the essential technology being developed/tested in the project", key=k("tech_descr"))

        st.markdown("### Technological maturity (TRL - Technology Readiness Level)")
        trl_start   = st.number_input("TRL at project start", min_value=1, max_value=9, step=1, key=k("trl_start"))
        trl_current = st.number_input("TRL currently",       min_value=1, max_value=9, step=1, key=k("trl_current"))
        trl_increase_reason = st.text_area("What has caused the increase in TRL level?", help="Only fill if TRL increased.", key=k("trl_increase_reason"))

        st.markdown("### Contribution to overall goals")
        extent_opts = ["To a great extent","To some extent","To a lesser extent","To a small extent","Not at all"]
        contrib_project = st.radio(
            'Has the project itself contributed to getting closer to this long term inflection point?\n'
            'Denmark becomes an operational European CO₂ storage hub with >10 Mtpa injection capacity (2030–2035)',
            extent_opts,
            key=k("contrib_project")
        )
        contrib_project_how = st.text_area("How/why? (please describe)", key=k("contrib_project_how"))

        contrib_society = st.radio("Has the technological/market development in society got nearer the inflection point?", extent_opts, key=k("contrib_society"))
        contrib_society_how = st.text_area("How/Why? What are the main challenges to get nearer to the inflection point?", key=k("contrib_society_how"))

        st.markdown("### Project indicators")
        yn_opts = ["Yes","No","Indeterminate/Unknown","Not relevant to the project"]

        st.markdown("##### Site characterization")
        site_char = st.radio("Has the project contributed to improvement of methods for site characterization, injectivity, and storage capacity estimation?", yn_opts, horizontal=True, key=k("site_char"))
        site_char_how = st.text_area("If yes, how?", key=k("site_char_how"))

        st.markdown("##### Safety and reliability")
        safety = st.radio("Has the project developed and improved methods for ensuring the safety and reliability of geological CO₂ storage?", yn_opts, horizontal=True, key=k("safety"))
        monitoring = st.radio("Has the project improved methods for reservoir monitoring and modeling of geological carbon storage?", yn_opts, horizontal=True, key=k("monitoring"))
        monitoring_how = st.text_area("If yes, how?", key=k("monitoring_how"))

        st.markdown("##### Dissolution and precipitation")
        diss_precip = st.radio("Has the project improved the prediction of dissolution and precipitation in chalk reservoirs to guide safe CO₂ injection?", yn_opts, horizontal=True, key=k("diss_precip"))
        diss_precip_how = st.text_area("If yes, how?", key=k("diss_precip_how"))

        st.markdown("##### Modelling and simulation")
        modelling = st.radio("Has the project developed and improved methods for modelling and simulation of the physical or geochemical behavior of CO₂?", yn_opts, horizontal=True, key=k("modelling"))
        modelling_how = st.text_area("If yes, how?", key=k("modelling_how"))

        st.markdown("##### Salt precipitation and injectivity")
        salt_precip = st.radio("Has the project improved mitigation of the effects of salt precipitation on CO₂ injectivity in the storage formation?", yn_opts, horizontal=True, key=k("salt_precip"))
        salt_precip_how = st.text_area("If yes, how?", key=k("salt_precip_how"))

        st.markdown("##### Corrosion management")
        corrosion = st.radio("Has the project introduced new techniques or technologies to assess and mitigate corrosion in CO₂ compression and injection infrastructure?", yn_opts, horizontal=True, key=k("corrosion"))
        corrosion_how = st.text_area("If yes, how?", key=k("corrosion_how"))

        st.markdown("##### Demonstration in operational environment")
        demo = st.radio("Has the project’s technological solution been fully developed and demonstrated in an operational environment?", ["Yes","No","Indeterminate/Unknown"], horizontal=True, key=k("demo"))
        demo_challenges = st.text_area("What are the challenges to be overcome to demonstrate it in an operational environment?", key=k("demo_challenges"))

        st.markdown("##### Scaling potential")
        scale_opts = ["Yes","No","Indeterminate/Unknown"]
        scalable = st.radio("Is the project’s tested technology scalable to store CO₂ in million tonnes per year?", scale_opts, horizontal=True, key=k("scalable"))
        scale_barriers = st.text_area("What are the main challenges/barriers to be overcome to reach such upscaling?", key=k("scale_barriers"))

        st.markdown("### Final reflections")
        gap_opts = ["Yes","No","Indeterminate/Unknown"]
        knowledge_gaps = st.radio("Has your project identified any specific knowledge gaps, limitations, or challenges encountered during its implementation that should be addressed in future INNO-CCUS projects or initiatives?", gap_opts, horizontal=True, key=k("knowledge_gaps"))
        knowledge_gaps_descr = st.text_area("If yes, please describe them and suggest potential approaches or areas for further investigation.", key=k("knowledge_gaps_descr"))

        add = st.form_submit_button("Add tracking entry", key=k("submit"))

    payload = {
        "project_id": selected_project_id,
        "status": status,
        "unforeseen_challenges": (unforeseen == "Yes"),
        "challenges": _none_if(unforeseen == "Yes", (challenges.strip() or None)),
        "resource_constraints": (res_constr == "Yes"),
        "constraints_selected": _none_if(res_constr == "Yes", (", ".join(constraints_sel) or None)),
        "constraints_other": _none_if(res_constr == "Yes", (constraints_other.strip() or None)),
        "storage_types": (", ".join(storage_types) or None),
        "injection_monitoring": (", ".join(injection_monitoring) or None),
        "tech_description": (tech_descr.strip() or None),
        "trl_start": int(trl_start),
        "trl_current": int(trl_current),
        "trl_increase_reason": _none_if(trl_current > trl_start, (trl_increase_reason.strip() or None)),
        "contrib_project": contrib_project,
        "contrib_project_how": (contrib_project_how.strip() or None),
        "contrib_society": contrib_society,
        "contrib_society_how": (contrib_society_how.strip() or None),
        "site_char": site_char,
        "site_char_how": (site_char_how.strip() or None),
        "safety": safety,
        "monitoring": monitoring,
        "monitoring_how": (monitoring_how.strip() or None),
        "diss_precip": diss_precip,
        "diss_precip_how": (diss_precip_how.strip() or None),
        "modelling": modelling,
        "modelling_how": (modelling_how.strip() or None),
        "salt_precip": salt_precip,
        "salt_precip_how": (salt_precip_how.strip() or None),
        "corrosion": corrosion,
        "corrosion_how": (corrosion_how.strip() or None),
        "demo": demo,
        "demo_challenges": (demo_challenges.strip() or None),
        "scalable": scalable,
        "scale_barriers": (scale_barriers.strip() or None),
        "knowledge_gaps": knowledge_gaps,
        "knowledge_gaps_descr": (knowledge_gaps_descr.strip() or None),
    }
    return add, payload

def render_ws4_tracking_form(selected_project_id: str):
    def _none_if(cond, val):
        return (val if cond else None)

    k = key_factory("ws4", selected_project_id)

    with st.form(f"ws4_tracking_form:{selected_project_id}", clear_on_submit=True):
        st.markdown("<h1 style='text-align: center;'>Workstream 4 - CO₂ Utilisation</h1>", unsafe_allow_html=True)
        st.markdown("### Project status and progression")

        status = st.selectbox("What is the current status of the project?",
        [
        "Green - Project is progressing according to current project plan",
        "Yellow - Project is mostly progressing according to current project plan with minor changes or delays",
        "Red - Changes and delays cause the project to diverge from the current project plan"
        ], key=k("status"))

        unforeseen = st.radio("Have any unforeseen challenges arisen during the project?", ["No","Yes"], horizontal=True, key=k("unforeseen"))
        challenges = st.text_area("If yes, what challenges?", help="Only fill this if you selected 'Yes' above.", key=k("challenges"))

        res_constr = st.radio("Are there any resource constraints affecting the progress of the project?", ["No","Yes"], horizontal=True, key=k("res_constr"))
        constraints_sel = st.multiselect("If Yes, which constraints?", ["Personnel","Funding","Equipment"], help="Only select if you answered 'Yes' above.", key=k("constraints_sel"))
        constraints_other = st.text_input("Other constraints", help="Only fill if 'Yes' above.", key=k("constraints_other"))

        st.markdown("### The project's technology development")
        chem_conv = st.multiselect(
            "Chemical Conversion methods being developed/tested?",
            [
                "Hydrogenation to fuels (methanol, methane, synthetic gasoline/diesel)",
                "Production of chemicals (urea, formic acid, polymers)",
                "Mineralization into construction materials (concrete, aggregates)",
            ],
            key=k("chem_conv")
        )
        bio_conv = st.multiselect(
            "Biological Conversion methods being developed/tested?",
            [
                "Algae cultivation for biofuels, feed, or bioproducts",
                "Microbial fermentation to chemicals (ethanol, acetate, proteins)",
                "Enhanced photosynthesis in plants or microbes",
            ],
            key=k("bio_conv")
        )
        electro_conv = st.multiselect(
            "Electrochemical and Photochemical Conversion methods being developed/tested?",
            [
                "Electrochemical reduction to fuels or chemicals (using electricity)",
                "Photocatalytic (solar-driven) conversion to fuels or chemicals",
            ],
            key=k("electro_conv")
        )
        direct_util = st.multiselect(
            "Direct Utilisation (Physical Use) methods being developed/tested?",
            [
                "Use of CO₂ as an industrial fluid or solvent (e.g., supercritical CO₂ for cleaning, extraction, or refrigeration)",
            ],
            key=k("direct_util")
        )
        tech_descr = st.text_area("Briefly describe the essential technology being developed/tested in the project", key=k("tech_descr"))

        st.markdown("### Technological maturity (TRL - Technology Readiness Level)")
        trl_start   = st.number_input("TRL at project start", min_value=1, max_value=9, step=1, key=k("trl_start"))
        trl_current = st.number_input("TRL currently",       min_value=1, max_value=9, step=1, key=k("trl_current"))
        trl_increase_reason = st.text_area("What has caused the increase in TRL level?", help="Only fill if TRL increased.", key=k("trl_increase_reason"))

        st.markdown("### Contribution to overall goals")
        extent_opts = ["To a great extent","To some extent","To a lesser extent","To a small extent","Not at all"]
        contrib_project = st.radio(
            'Has the project itself contributed to getting closer to this long term inflection point?\n'
            'A commercial market for CO₂-based materials achieves self-sustaining growth, by 2045.',
            extent_opts,
            key=k("contrib_project")
        )
        contrib_project_how = st.text_area("How/why? (please describe)", key=k("contrib_project_how"))

        contrib_society = st.radio("Has the technological/market development in society got nearer the inflection point?", extent_opts, key=k("contrib_society"))
        contrib_society_how = st.text_area("How/Why? What are the main challenges to get nearer to the inflection point?", key=k("contrib_society_how"))

        st.markdown("### Project indicators")
        yn_opts = ["Yes","No","Indeterminate/Unknown","Not relevant to the project"]

        st.markdown("##### Development of new products")
        new_chem_prod = st.radio("Has the project developed or demonstrated the production of new high-value chemicals or platform molecules from CO₂?", yn_opts, horizontal=True, key=k("new_chem_prod"))
        new_chem_prod_descr = st.text_area("If yes, describe the product:", key=k("new_chem_prod_descr"))

        new_co2_prod = st.radio("Has the project developed new types of CO₂-based products?", yn_opts, horizontal=True, key=k("new_co2_prod"))
        new_co2_prod_descr = st.text_area("If yes, describe the product:", key=k("new_co2_prod_descr"))

        st.markdown("##### Energy Efficiency")
        energy_kwh = st.number_input("Total energy consumption per metric ton of product (kWh/t product)", min_value=0.0, step=1.0, key=k("energy_kwh"))
        energy_improved = st.radio("Has there been an increase in the energy efficiency of the tested technology since project start?", yn_opts, horizontal=True, key=k("energy_improved"))
        energy_from = st.number_input("Energy efficiency at project start (%)", min_value=0.0, max_value=100.0, step=0.5, key=k("energy_from"))
        energy_to   = st.number_input("Energy efficiency now (%)",   min_value=0.0, max_value=100.0, step=0.1, key=k("energy_to"))
        energy_steps = st.text_area("Which steps in the process are most energy-intensive, and are there opportunities for efficiency improvements?", key=k("energy_steps"))

        st.markdown("##### Cost efficiency")
        cost_dkk = st.number_input("Cost of producing 1 ton of the new material/product (DKK)", min_value=0.0, step=1.0, key=k("cost_dkk"))
        cost_improved = st.radio("Has there been an improvement of the cost efficiency of the tested technology since project start?", yn_opts, horizontal=True, key=k("cost_improved"))
        cost_from = st.number_input("Cost efficiency at project start (%)", min_value=0.0, max_value=100.0, step=0.5, key=k("cost_from"))
        cost_to   = st.number_input("Cost efficiency now (%)",   min_value=0.0, max_value=100.0, step=0.1, key=k("cost_to"))

        cost_alt_improved = st.radio("Has your project developed solutions that have reduced the cost of converting CO₂ to new products or materials?", yn_opts, horizontal=True, key=k("cost_alt_improved"))
        cost_alt_how = st.text_area("If yes, how?", key=k("cost_alt_how"))

        st.markdown("##### Improved processes")
        proc_improved = st.radio("Has the project contributed to the development of new or improved processes using captured CO₂ as a feedstock?", yn_opts, horizontal=True, key=k("proc_improved"))
        proc_improved_how = st.text_area("If yes, how?", key=k("proc_improved_how"))

        st.markdown("##### Scaling potential and industrial adoption")
        scale_demo = st.radio("Has the project’s technology of conversion of CO₂ moved closer to demonstration scale and industrial adoption?", yn_opts, horizontal=True, key=k("scale_demo"))
        scale_demo_challenges = st.text_area("What are the main challenges to achieve this?", key=k("scale_demo_challenges"))

        scale_market = st.radio("Has the project’s CO₂ based products/materials moved closer to becoming market-ready CO₂-based products?", yn_opts, horizontal=True, key=k("scale_market"))
        scale_market_challenges = st.text_area("What are the main challenges to achieve this?", key=k("scale_market_challenges"))

        st.markdown("### Final reflections")
        gap_opts = ["Yes","No","Indeterminate/Unknown","Not relevant to the project"]
        knowledge_gaps = st.radio("Has your project identified any specific knowledge gaps, limitations, or challenges encountered during its implementation that should be addressed in future INNO-CCUS projects or initiatives?", gap_opts, horizontal=True, key=k("knowledge_gaps"))
        knowledge_gaps_descr = st.text_area("If yes, please describe them and suggest potential approaches or areas for further investigation.", key=k("knowledge_gaps_descr"))

        add = st.form_submit_button("Add tracking entry", key=k("submit"))

    payload = {
        "project_id": selected_project_id,
        "status": status,
        "unforeseen_challenges": (unforeseen == "Yes"),
        "challenges": _none_if(unforeseen == "Yes", (challenges.strip() or None)),
        "resource_constraints": (res_constr == "Yes"),
        "constraints_selected": _none_if(res_constr == "Yes", (", ".join(constraints_sel) or None)),
        "constraints_other": _none_if(res_constr == "Yes", (constraints_other.strip() or None)),
        "chem_conv": (", ".join(chem_conv) or None),
        "bio_conv": (", ".join(bio_conv) or None),
        "electro_conv": (", ".join(electro_conv) or None),
        "direct_util": (", ".join(direct_util) or None),
        "tech_description": (tech_descr.strip() or None),
        "trl_start": int(trl_start),
        "trl_current": int(trl_current),
        "trl_increase_reason": _none_if(trl_current > trl_start, (trl_increase_reason.strip() or None)),
        "contrib_project": contrib_project,
        "contrib_project_how": (contrib_project_how.strip() or None),
        "contrib_society": contrib_society,
        "contrib_society_how": (contrib_society_how.strip() or None),
        "energy_kwh_per_ton": float(energy_kwh),
        "energy_eff_improved": energy_improved,
        "energy_eff_from_pct": float(energy_from),
        "energy_eff_to_pct": float(energy_to),
        "energy_steps": (energy_steps.strip() or None),
        "cost_dkk_per_ton": float(cost_dkk),
        "cost_improved": cost_improved,
        "cost_eff_from_pct": float(cost_from),
        "cost_eff_to_pct": float(cost_to),
        "cost_alt_improved": cost_alt_improved,
        "cost_alt_how": (cost_alt_how.strip() or None),
        "proc_improved": proc_improved,
        "proc_improved_how": (proc_improved_how.strip() or None),
        "scale_demo": scale_demo,
        "scale_demo_challenges": (scale_demo_challenges.strip() or None),
        "scale_market": scale_market,
        "scale_market_challenges": (scale_market_challenges.strip() or None),
        "knowledge_gaps": knowledge_gaps,
        "knowledge_gaps_descr": (knowledge_gaps_descr.strip() or None),
    }
    return add, payload

def render_ws5_tracking_form(selected_project_id: str):
    def _none_if(cond, val):
        return (val if cond else None)

    k = key_factory("ws5", selected_project_id)

    with st.form(f"ws5_tracking_form:{selected_project_id}", clear_on_submit=True):
        st.markdown("<h1 style='text-align: center;'>Workstream 5 - Society and Systems Analysis</h1>", unsafe_allow_html=True)
        st.markdown("### Project status and progression")

        status = st.selectbox(
            "What is the current status of the project?",
            [
                "Green - Project is progressing according to current project plan",
                "Yellow - Project is mostly progressing according to current project plan with minor changes or delays",
                "Red - Changes and delays cause the project to diverge from the current project plan"
                ],
            key=k("status")
        )

        unforeseen = st.radio("Have any unforeseen challenges arisen during the project?", ["No","Yes"], horizontal=True, key=k("unforeseen"))
        challenges = st.text_area("If yes, what challenges?", help="Only fill this if you selected 'Yes' above.", key=k("challenges"))

        res_constr = st.radio("Are there any resource constraints affecting the progress of the project?", ["No","Yes"], horizontal=True, key=k("res_constr"))
        constraints_sel = st.multiselect("If Yes, which constraints?", ["Personnel","Funding","Equipment"], help="Only select if you answered 'Yes' above.", key=k("constraints_sel"))
        constraints_other = st.text_input("Other constraints", help="Only fill if 'Yes' above.", key=k("constraints_other"))

        st.markdown("### The project's activities")
        activities = st.multiselect(
            "What types of activities are included in your project?",
            [
                "Public acceptance analysis",
                "Socio-economic and behavioral research",
                "Stakeholder and citizen involvement",
                "System integration analysis",
                "Geospatial and infrastructure assessment",
                "Value chain and market analysis",
                "Policy and regulatory analysis",
                "Environmental and climate impact assessment",
                "Deployment strategy development",
            ],
            key=k("activities")
        )
        activities_other = st.text_area("Other types of activities than mentioned above:", key=k("activities_other"))

        st.markdown("### Contribution to overall goals")
        extent_opts = ["To a great extent","To some extent","To a lesser extent","To a small extent","Not at all"]
        contrib_project = st.radio(
            'Has the project contributed to getting closer to this long term inflection point?\n'
            'Societal and local support ensures broad implementation of CCUS infrastructure in Denmark. (2045)',
            extent_opts,
            key=k("contrib_project")
        )
        contrib_project_how = st.text_area("How/why? (please describe)", key=k("contrib_project_how"))

        contrib_society = st.radio("Has the development in the society got nearer the inflection point?", extent_opts, key=k("contrib_society"))
        contrib_society_how = st.text_area("How/Why? What are the main challenges to get nearer to the inflection point?", key=k("contrib_society_how"))

        st.markdown("### Project indicators")
        yn_opts = ["Yes","No","Undeterminate/unknown","Not relevant to project"]

        st.markdown("##### Understanding and Enhancing Public Support")
        public_support_factors = st.radio("Has your project identified key factors that influence public willingness to support or pay for CCUS installations?", yn_opts, horizontal=True, key=k("public_support_factors"))
        public_support_findings = st.text_area("If yes, what are key findings?", key=k("public_support_findings"))
        public_support_enabling = st.radio("Has the project contributed to create enabling conditions for public support of CCUS solutions?", yn_opts, horizontal=True, key=k("public_support_enabling"))
        public_support_enabling_how = st.text_area("If yes, how?", key=k("public_support_enabling_how"))

        st.markdown("##### Reduction of uncertainty")
        uncertainty_reduction = st.radio("Has the project contributed to reduce uncertainty and perceived risk among stakeholders through demonstrable safe operation?", yn_opts, horizontal=True, key=k("uncertainty_reduction"))
        uncertainty_reduction_how = st.text_area("If yes, how?", key=k("uncertainty_reduction_how"))

        st.markdown("##### Guidelines for Policy Making")
        guidelines_policy = st.radio("Has your project developed practical guidelines for policymakers and local authorities on the siting and engagement of CCUS facilities?", yn_opts, horizontal=True, key=k("guidelines_policy"))
        guidelines_policy_findings = st.text_area("If yes, what are key guidelines?", key=k("guidelines_policy_findings"))

        st.markdown("##### Evidence for System Integration and Strategic Planning")
        system_integration = st.radio("Has your project validated strategies for integrating CCUS facilities with existing local infrastructure (e.g., district heating, legacy grids)?", yn_opts, horizontal=True, key=k("system_integration"))
        system_integration_how = st.text_area("If yes, how?", key=k("system_integration_how"))
        minimize_disruption = st.radio("Has your project provided criteria or analyses to help minimize local disruption and maximize societal and economic benefits from CCUS system integration?", yn_opts, horizontal=True, key=k("minimize_disruption"))
        minimize_disruption_how = st.text_area("If yes, how?", key=k("minimize_disruption_how"))

        st.markdown("##### Developing Approaches for Co-Creation with Communities and Stakeholders")
        cocreation = st.radio("Has your project established partnership models or co-creation approaches with local communities and stakeholders in CCUS planning?", yn_opts, horizontal=True, key=k("cocreation"))
        cocreation_how = st.text_area("If yes, how?", key=k("cocreation_how"))

        st.markdown("### Final reflections")
        knowledge_gaps_descr = st.text_area("Has your project identified any specific knowledge gaps, limitations, or challenges encountered during its implementation that should be addressed in future INNO-CCUS projects or initiatives? If so, please describe them and suggest potential approaches or areas for further investigation.", key=k("knowledge_gaps_descr"))

        add = st.form_submit_button("Add tracking entry", key=k("submit"))

    payload = {
        "project_id": selected_project_id,
        "status": status,
        "unforeseen_challenges": (unforeseen == "Yes"),
        "challenges": _none_if(unforeseen == "Yes", (challenges.strip() or None)),
        "resource_constraints": (res_constr == "Yes"),
        "constraints_selected": _none_if(res_constr == "Yes", (", ".join(constraints_sel) or None)),
        "constraints_other": _none_if(res_constr == "Yes", (constraints_other.strip() or None)),
        "activities": (", ".join(activities) or None),
        "activities_other": (activities_other.strip() or None),
        "contrib_project": contrib_project,
        "contrib_project_how": (contrib_project_how.strip() or None),
        "contrib_society": contrib_society,
        "contrib_society_how": (contrib_society_how.strip() or None),
        "public_support_factors": public_support_factors,
        "public_support_findings": (public_support_findings.strip() or None),
        "public_support_enabling": public_support_enabling,
        "public_support_enabling_how": (public_support_enabling_how.strip() or None),
        "uncertainty_reduction": uncertainty_reduction,
        "uncertainty_reduction_how": (uncertainty_reduction_how.strip() or None),
        "guidelines_policy": guidelines_policy,
        "guidelines_policy_findings": (guidelines_policy_findings.strip() or None),
        "system_integration": system_integration,
        "system_integration_how": (system_integration_how.strip() or None),
        "minimize_disruption": minimize_disruption,
        "minimize_disruption_how": (minimize_disruption_how.strip() or None),
        "cocreation": cocreation,
        "cocreation_how": (cocreation_how.strip() or None),
        "knowledge_gaps_descr": (knowledge_gaps_descr.strip() or None),
    }
    return add, payload

# =========================
# Set proxy
# =========================
os.environ['http_proxy']  = 'http://squid18.localdom.net:3128'
os.environ['https_proxy'] = 'http://squid18.localdom.net:3128'

# =========================
# Config
# =========================
PARENT_TABLE = "Projekt_Data" 

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://ugfsmunvwyddfkuvlxye.supabase.co")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVnZnNtdW52d3lkZGZrdXZseHllIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTIxMzg3OTUsImV4cCI6MjA2NzcxNDc5NX0.FOMjr4gebKrxJ_zq_fgmSXA4cu4aefdKN0QUlxv_Ruo") 

st.set_page_config(page_title="CCUS Project Tracker", page_icon="📈", layout="wide")
st.title("CCUS Project Tracker")

# =========================
# Supabase client
# =========================
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# ============ Auth helpers ============
def current_user_is_admin() -> bool:
    try:
        u = supabase.auth.get_user()
        user = getattr(u, "user", None)
        meta = getattr(user, "app_metadata", {}) if user else {}
        is_sup = meta.get("is_super_admin")
        role = (meta.get("role") or "").lower()
        return (str(is_sup).lower() == "true") or (role == "admin")
    except Exception:
        return False

def hydrate_token_from_session():
    token = st.session_state.get("sb_token")
    refresh = st.session_state.get("sb_refresh")
    if token:
        try:
            supabase.postgrest.auth(token)
            supabase.auth.set_session(token, refresh or "")
        except Exception:
            pass
    # refresh admin flag on hydrate
    st.session_state["is_admin"] = st.session_state.get("is_admin", current_user_is_admin())

hydrate_token_from_session()

def rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

def do_login(email: str, password: str):
    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
    if not res or not getattr(res, "session", None):
        raise RuntimeError("Login returned no session. Check credentials or email confirmation.")
    token = res.session.access_token
    refresh = res.session.refresh_token
    st.session_state["sb_token"] = token
    st.session_state["sb_refresh"] = refresh
    supabase.postgrest.auth(token)
    try:
        supabase.auth.set_session(token, refresh)
    except Exception:
        pass
    # set admin flag after login
    st.session_state["is_admin"] = current_user_is_admin()

def is_logged_in() -> bool:
    return bool(st.session_state.get("sb_token"))

def logout():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    st.session_state.pop("sb_token", None)
    st.session_state.pop("sb_refresh", None)
    st.session_state.pop("is_admin", None)

# Helpers for diff/apply
def is_na(x):
    try:
        return (x is None) or (isinstance(x, float) and math.isnan(x)) or pd.isna(x)
    except Exception:
        return False

def sanitize_value(v):
    # Convert NaN/empty string to None, keep other values as-is
    if is_na(v):
        return None
    if isinstance(v, str) and v.strip() == "":
        return None
    # Convert numpy scalars to native
    try:
        import numpy as np
        if isinstance(v, (np.generic,)):
            return v.item()
    except Exception:
        pass
    return v

# =========================
# LOGIN
# =========================
if not is_logged_in():
    st.subheader("Sign in")
    with st.form("login", clear_on_submit=False):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        ok = st.form_submit_button("Sign in")
        if ok:
            try:
                do_login(email, password)
                st.success("Signed in.")
                rerun()
            except Exception as e:
                st.error(f"Sign-in failed: {e}")
    st.stop()

IS_ADMIN = bool(st.session_state.get("is_admin"))

# --- Tabs (visualisations only for admins) ---
if IS_ADMIN:
    tab1, tab2, tab3 = st.tabs(["Your Projects", "Track Projects", "Visualisations"])
else:
    tab1, tab2 = st.tabs(["Your Projects", "Track Projects"])

with tab1:
    # --- Projects Table Section ---

    # =========================
    # LOAD USER ROWS (RLS will filter to owned rows; admins see all)
    # =========================
    try:
        resp = supabase.table(PARENT_TABLE).select("*").order("created_at", desc=True).execute()
        rows = resp.data or []
    except Exception as e:
        st.error(f"Could not load project data: {e}")
        rows = []

    if not rows:
        st.info("No projects assigned to your user.")
        st.markdown("---")
        if st.button("Sign out"):
            logout()
            st.query_params.clear()
            rerun()
        st.stop()

    # Convert to DataFrame; keep id for updates but HIDE it in the editor
    df = pd.DataFrame(rows)

    # Ensure 'id' exists and is unique to use as hidden index
    if "id" not in df.columns:
        st.error("Expected 'id' column not found in table.")
        st.stop()

    # Save original for diffing
    df_orig = df.copy()

    # Use 'id' as index for diff/update, but hide it in the UI
    df = df.set_index("id", drop=True)

    # Hide owner_id and id in the editor (id is index; we'll hide the index)
    cols_display = [c for c in df.columns if c.lower() != "owner_id"]

    st.subheader("Your projects (editable)")
    edited = st.data_editor(
        df[cols_display],
        num_rows="fixed",                # prevent adding rows from UI
        use_container_width=True,
        hide_index=True,                 # id stays hidden
    )

    # Button to save changes back to Supabase
    if st.button("Save table changes"):
        if edited is None or edited.empty:
            st.info("Nothing to save.")
        else:
            # Diff vs original
            updated_count = 0
            # Align original display df
            df_disp_orig = df_orig.set_index("id", drop=True)[cols_display]
            # Iterate rows by id
            for rid in edited.index:
                if rid not in df_disp_orig.index:
                    continue
                orig_row = df_disp_orig.loc[rid]
                new_row  = edited.loc[rid]
                changes = {}
                for col in cols_display:
                    a, b = orig_row.get(col), new_row.get(col)
                    # Treat NaN == NaN
                    if (is_na(a) and is_na(b)) or (a == b):
                        continue
                    changes[col] = sanitize_value(b)
                # Apply update if any changed columns
                if changes:
                    try:
                        supabase.table(PARENT_TABLE).update(changes).eq("id", str(rid)).execute()
                        updated_count += 1
                    except Exception as e:
                        st.error(f"Update failed for row {rid}: {e}")
            if updated_count:
                st.success(f"Saved changes on {updated_count} row(s).")
                rerun()
            else:
                st.info("No changes detected.")

    st.markdown("---")

    # ======= ADD NEW PROJECT (via def) =======
    if IS_ADMIN:
        st.markdown("<h1 style='text-align: center;'>Add a new project</h1>", unsafe_allow_html=True)
        create_ok, np_fields = render_new_project_form()

        if create_ok:
            np_navn  = np_fields["np_navn"]
            np_akr   = np_fields["np_akr"]
            np_pool  = np_fields["np_pool"]
            np_ws    = np_fields["np_ws"]
            np_start = np_fields["np_start"]
            np_slut  = np_fields["np_slut"]
            np_leder = np_fields["np_leder"]
            np_varig = np_fields["np_varig"]
            np_form  = np_fields["np_form"]
            np_budget= np_fields["np_budget"]

            errs = []
            if not np_navn.strip():
                errs.append("ProjektNavn er påkrævet.")
            if np_slut and (np_slut < np_start):
                errs.append("Slut skal være efter Start.")
            if errs:
                for e in errs: st.warning(e)
            else:
                try:
                    # IMPORTANT: do NOT send owner_id – DB trigger sets it to auth.uid()
                    payload = {
                        "ProjektNavn": np_navn.strip(),
                        "Projektakronym": (np_akr.strip() or None),
                        "Pool": float(np_pool) if np_pool is not None else None,
                        "Projektleder": (np_leder.strip() or None),
                        "Workstream": int(np_ws) if np_ws is not None else None,
                        "Varighed": (np_varig.strip() or None),
                        "Formål/Beskrivelse": (np_form.strip() or None),
                        "Start": str(np_start) if np_start else None,
                        "Slut": str(np_slut) if np_slut else None,
                        "Budget": float(np_budget) if np_budget is not None else None,
                    }
                    ins = supabase.table(PARENT_TABLE).insert(payload).execute()
                    if ins.data:
                        st.success("Projekt oprettet ✅")
                        st.session_state["show_new_project_form"] = False
                        rerun()
                    else:
                        st.error("Insert returned no data.")
                except Exception as e:
                    st.error(f"Kunne ikke oprette projekt: {e}")

with tab2:
    st.markdown("### Track project progress")

    # Forudsætning: df indeholder dine projekter og har index = projekt_id (uuid)
    # Hvis ikke, så hent dem her:
    if 'df' not in locals() or df is None or df.empty:
        try:
            proj = supabase.table("Projekt_Data").select("*").execute().data or []
            df = pd.DataFrame(proj)
            if "id" in df.columns:
                df = df.set_index("id")
        except Exception as e:
            st.error(f"Kunne ikke hente projekter: {e}")
            st.stop()

    # Simpel selector
    if df.empty:
        st.info("Ingen projekter fundet.")
        st.stop()

    # Vælg visningskolonne til label i selectbox (brug det du har)
    label_col = next((c for c in ["ProjektNavn","Projekt_Navn","Project_Name","Name","title","navn"] if c in df.columns), None)
    proj_options = df.index.tolist()
    proj_labels = [df.at[i,label_col] if label_col else str(i) for i in proj_options]
    selected_project_id = st.selectbox("Vælg projekt", proj_options, format_func=lambda x: proj_labels[proj_options.index(x)])


    # Find projektets workstream (kræver kolonne "Workstream")
    selected_row = df.loc[selected_project_id] if selected_project_id in df.index else None
    workstream = int(selected_row.get("Workstream")) if (selected_row is not None and pd.notna(selected_row.get("Workstream"))) else None

    # Map WS -> tabelnavn og form-funktion
    ws_map = {
        1: ("Tracking_WS1", render_ws1_tracking_form),
        2: ("Tracking_WS2", render_ws2_tracking_form),
        3: ("Tracking_WS3", render_ws3_tracking_form),
        4: ("Tracking_WS4", render_ws4_tracking_form),
        5: ("Tracking_WS5", render_ws5_tracking_form),
    }

    if workstream not in ws_map:
        st.warning("Workstream for valgt projekt er ikke angivet eller ikke understøttet.")
        st.stop()

    table_name, form_fn = ws_map[workstream]

    # Hent eksisterende entries (kun for den relevante WS-tabel)
    try:
        entries = (
            supabase.table(table_name)
            .select("*")
            .eq("project_id", str(selected_project_id))
            .order("Timestamp", desc=True)
            .execute()
            .data or []
        )
        if entries:
            st.write("Seneste tracking-entries:")
            st.dataframe(pd.DataFrame(entries), width="stretch")
        else:
            st.info("Ingen tracking-entries for dette projekt endnu.")
    except Exception as e:
        st.error(f"Kunne ikke hente tracking-entries: {e}")

    # Render korrekt WS-form og indsæt i korrekt tabel
    add, payload = form_fn(str(selected_project_id))
    if add and payload:
        try:
            ins = supabase.table(table_name).insert(payload).execute()
            if ins.data is not None:
                st.success("Tracking entry tilføjet ✅")
                st.rerun()
            else:
                st.error("Insert returnerede ingen data.")
        except Exception as e:
            st.error(f"Kunne ikke indsætte tracking entry: {e}")

# =========================
# Tab 3: Visualisations (ADMIN ONLY) — projekt status
# =========================
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

def _latest_status_by_ws(table_name: str) -> pd.DataFrame:
    try:
        data = (
            supabase.table(table_name)
            .select("project_id,status,Timestamp")
            .order("project_id", desc=False)
            .order("Timestamp", desc=True)
            .execute()
            .data or []
        )
        if not data:
            return pd.DataFrame(columns=["project_id","status","Timestamp","ws"])
        d = pd.DataFrame(data)
        d["ws"] = int(table_name[-1])  # antager 'Tracking_WSn'
        d = d.sort_values(["project_id","Timestamp"], ascending=[True, False]).drop_duplicates("project_id", keep="first")
        return d[["project_id","status","Timestamp","ws"]]
    except Exception:
        return pd.DataFrame(columns=["project_id","status","Timestamp","ws"])

with tab3:
    st.markdown("### Status på projekter ")

    # Projekter
    proj = supabase.table("Projekt_Data").select("*").execute().data or []
    if not proj:
        st.info("Ingen projekter fundet.")
        st.stop()
    projects_df = pd.DataFrame(proj)

    # Tjek kolonner
    if "id" not in projects_df.columns or "Workstream" not in projects_df.columns:
        st.error("Projekt_Data skal have kolonnerne 'id' og 'Workstream'.")
        st.stop()

    # Find projekt-navn kolonne (præference: 'ProjektNavn')
    name_col = "ProjektNavn" if "ProjektNavn" in projects_df.columns else \
               next((c for c in ["Projekt_Navn","Project_Name","Name","title","navn"] if c in projects_df.columns), None)

    # Hent seneste status fra alle tracking-tabeller
    ws_tables = ["Tracking_WS1","Tracking_WS2","Tracking_WS3","Tracking_WS4","Tracking_WS5"]
    latest_df = pd.concat([_latest_status_by_ws(t) for t in ws_tables], ignore_index=True) \
                if ws_tables else pd.DataFrame(columns=["project_id","status","Timestamp","ws"])

    # Merge så projekter UDEN status stadig vises (status=blank)
    merged = projects_df.merge(
        latest_df,
        left_on=["id","Workstream"],
        right_on=["project_id","ws"],
        how="left",
        suffixes=("","_latest")
    )

    # Byg visnings-DF
    disp_cols = ["id", "Workstream"]
    if name_col: disp_cols.insert(1, name_col)
    disp_cols += ["status", "Timestamp"]

    overview = merged[disp_cols].copy()
    overview = overview.rename(columns={
        "id": "Project ID",
        "Workstream": "WS",
        name_col if name_col else "Project": "ProjektNavn",
        "status": "Status",
        "Timestamp": "Last Update"
    })

    # Farv rækker efter Status
    row_style_js = JsCode("""
    function(params) {
      const s = (params.data.Status || "").toLowerCase();
      if (s.startsWith("green"))  { return {'background-color': '#e8f5e9'}; }   // light green
      if (s.startsWith("yellow")) { return {'background-color': '#fff8e1'}; }   // light yellow
      if (s.startsWith("red"))    { return {'background-color': '#ffebee'}; }   // light red
      return null; // ingen status -> ingen farve
    }
    """)

    gb = GridOptionsBuilder.from_dataframe(overview)
    gb.configure_grid_options(getRowStyle=row_style_js.js_code)
    gb.configure_columns({
        "Project ID": {"headerName": "Project ID", "width": 60},
        "WS": {"headerName": "WS", "width": 80, "type": ["numericColumn"]},
        "ProjektNavn": {"headerName": "ProjektNavn", "width": 380},
        "Status": {"headerName": "Status", "width": 340},
        "Last Update": {"headerName": "Last Update", "width": 200}
    })
    gb.configure_selection("none")
    gb.configure_side_bar(False)
    grid = AgGrid(
        overview,
        gridOptions=gb.build(),
        fit_columns_on_grid_load=True,
        allow_unsafe_jscode=True,   # kræves for getRowStyle
        theme="balham",
        height=520,
        width='stretch'  
    )

# =========================
# Sign out
# =========================
st.markdown("---")
if st.button("Sign out"):
    logout()
    st.query_params.clear()
    rerun()
