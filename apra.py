
import streamlit as st
import anthropic
import chromadb
import os
import math
import json
from datetime import datetime

st.set_page_config(page_title="APRA — Photonics Research Agent", page_icon="🤖", layout="wide")
st.title("🤖 APRA — Autonomous Photonics Research Assistant")
st.markdown("*Prof. Mustafa A.G. Abushagur, RIT — Powered by 51 Published Papers*")
st.divider()

api_key = os.environ.get("ANTHROPIC_API_KEY", "").replace(" ", "")
CHROMA_DIR = "/Users/mustafaabushagur/papers_chroma_db"

@st.cache_resource
def load_papers():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    return client.get_collection("papers")

collection = load_papers()

# Tool definitions
tools = [
    {
        "name": "search_papers",
        "description": "Search Professor Abushagur published papers for relevant information",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "calculate_fiber_loss",
        "description": "Calculate total fiber optic link loss",
        "input_schema": {
            "type": "object",
            "properties": {
                "length_km": {"type": "number"},
                "attenuation_db_km": {"type": "number"},
                "num_splices": {"type": "integer"},
                "splice_loss_db": {"type": "number"},
                "num_connectors": {"type": "integer"},
                "connector_loss_db": {"type": "number"}
            },
            "required": ["length_km", "attenuation_db_km"]
        }
    },
    {
        "name": "calculate_numerical_aperture",
        "description": "Calculate numerical aperture and V-number",
        "input_schema": {
            "type": "object",
            "properties": {
                "n_core": {"type": "number"},
                "n_clad": {"type": "number"},
                "core_diameter_um": {"type": "number"},
                "wavelength_um": {"type": "number"}
            },
            "required": ["n_core", "n_clad"]
        }
    },
    {
        "name": "calculate_dispersion",
        "description": "Calculate pulse broadening due to dispersion",
        "input_schema": {
            "type": "object",
            "properties": {
                "dispersion_ps_nm_km": {"type": "number"},
                "spectral_width_nm": {"type": "number"},
                "length_km": {"type": "number"},
                "bit_rate_gbps": {"type": "number"}
            },
            "required": ["dispersion_ps_nm_km", "spectral_width_nm", "length_km"]
        }
    },
    {
        "name": "calculate_power_budget",
        "description": "Calculate optical power budget and system margin",
        "input_schema": {
            "type": "object",
            "properties": {
                "tx_power_dbm": {"type": "number"},
                "rx_sensitivity_dbm": {"type": "number"},
                "total_loss_db": {"type": "number"},
                "safety_margin_db": {"type": "number"}
            },
            "required": ["tx_power_dbm", "rx_sensitivity_dbm", "total_loss_db"]
        }
    },
    {
        "name": "calculate_fbg_wavelength",
        "description": "Calculate Fiber Bragg Grating Bragg wavelength shift",
        "input_schema": {
            "type": "object",
            "properties": {
                "bragg_wavelength_nm": {"type": "number"},
                "strain_microstrain": {"type": "number"},
                "temperature_change_c": {"type": "number"},
                "gauge_factor": {"type": "number"},
                "thermal_coefficient": {"type": "number"}
            },
            "required": ["bragg_wavelength_nm"]
        }
    },
    {
        "name": "calculate_wdm_channels",
        "description": "Calculate WDM channel parameters",
        "input_schema": {
            "type": "object",
            "properties": {
                "center_wavelength_nm": {"type": "number"},
                "channel_spacing_ghz": {"type": "number"},
                "num_channels": {"type": "integer"},
                "bit_rate_gbps": {"type": "number"}
            },
            "required": ["center_wavelength_nm", "channel_spacing_ghz", "num_channels"]
        }
    },
    {
        "name": "calculate_coherence_length",
        "description": "Calculate source coherence length",
        "input_schema": {
            "type": "object",
            "properties": {
                "wavelength_nm": {"type": "number"},
                "spectral_width_nm": {"type": "number"}
            },
            "required": ["wavelength_nm", "spectral_width_nm"]
        }
    },
    {
        "name": "calculate_snr",
        "description": "Calculate optical signal to noise ratio",
        "input_schema": {
            "type": "object",
            "properties": {
                "signal_power_dbm": {"type": "number"},
                "noise_power_dbm": {"type": "number"},
                "bandwidth_ghz": {"type": "number"}
            },
            "required": ["signal_power_dbm", "noise_power_dbm"]
        }
    },
    {
        "name": "calculate_amplifier_gain",
        "description": "Calculate optical amplifier gain and noise figure",
        "input_schema": {
            "type": "object",
            "properties": {
                "input_power_dbm": {"type": "number"},
                "output_power_dbm": {"type": "number"},
                "noise_figure_db": {"type": "number"},
                "wavelength_nm": {"type": "number"}
            },
            "required": ["input_power_dbm", "output_power_dbm"]
        }
    },
    {
        "name": "generate_report",
        "description": "Generate a research report based on analysis",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string"},
                "format": {"type": "string", "enum": ["md", "txt"]}
            },
            "required": ["title", "content", "format"]
        }
    }
]

# Tool execution
def execute_tool(name, inputs):
    if name == "search_papers":
        results = collection.query(query_texts=[inputs["query"]], n_results=4)
        output = ""
        for i, doc in enumerate(results["documents"][0]):
            source = results["metadatas"][0][i]["source"]
            output += f"From {source}:\n{doc}\n\n"
        return output

    elif name == "calculate_fiber_loss":
        fiber = inputs["length_km"] * inputs["attenuation_db_km"]
        splice = inputs.get("num_splices", 0) * inputs.get("splice_loss_db", 0.1)
        connector = inputs.get("num_connectors", 0) * inputs.get("connector_loss_db", 0.5)
        total = fiber + splice + connector
        return json.dumps({
            "fiber_loss_db": round(fiber, 3),
            "splice_loss_db": round(splice, 3),
            "connector_loss_db": round(connector, 3),
            "total_loss_db": round(total, 3)
        })

    elif name == "calculate_numerical_aperture":
        NA = math.sqrt(inputs["n_core"]**2 - inputs["n_clad"]**2)
        angle = math.degrees(math.asin(min(NA, 1.0)))
        result = {"NA": round(NA, 4), "acceptance_angle_deg": round(angle, 3)}
        if "core_diameter_um" in inputs and "wavelength_um" in inputs:
            V = math.pi * inputs["core_diameter_um"] * NA / inputs["wavelength_um"]
            result["V_number"] = round(V, 3)
            result["mode"] = "single-mode" if V < 2.405 else "multimode"
        return json.dumps(result)

    elif name == "calculate_dispersion":
        broadening = abs(inputs["dispersion_ps_nm_km"]) * inputs["spectral_width_nm"] * inputs["length_km"]
        result = {"pulse_broadening_ps": round(broadening, 4)}
        if "bit_rate_gbps" in inputs:
            max_len = 1000 / (inputs["bit_rate_gbps"] * abs(inputs["dispersion_ps_nm_km"]) * inputs["spectral_width_nm"])
            result["max_length_km"] = round(max_len, 2)
        return json.dumps(result)

    elif name == "calculate_power_budget":
        available = inputs["tx_power_dbm"] - inputs["rx_sensitivity_dbm"]
        margin = available - inputs["total_loss_db"] - inputs.get("safety_margin_db", 3.0)
        return json.dumps({
            "available_power_db": round(available, 2),
            "system_margin_db": round(margin, 2),
            "status": "PASS" if margin > 0 else "FAIL"
        })

    elif name == "calculate_fbg_wavelength":
        lb = inputs["bragg_wavelength_nm"]
        strain = inputs.get("strain_microstrain", 0)
        temp = inputs.get("temperature_change_c", 0)
        gf = inputs.get("gauge_factor", 0.78)
        tc = inputs.get("thermal_coefficient", 6.67e-6)
        delta_strain = lb * gf * strain * 1e-6
        delta_temp = lb * tc * temp
        total_shift = delta_strain + delta_temp
        return json.dumps({
            "bragg_wavelength_nm": lb,
            "strain_shift_nm": round(delta_strain, 6),
            "temperature_shift_nm": round(delta_temp, 6),
            "total_shift_nm": round(total_shift, 6),
            "new_wavelength_nm": round(lb + total_shift, 6)
        })

    elif name == "calculate_wdm_channels":
        c = 3e8
        spacing_nm = (inputs["channel_spacing_ghz"] * 1e9 * 
                     (inputs["center_wavelength_nm"] * 1e-9)**2 / c) * 1e9
        channels = []
        n = inputs["num_channels"]
        for i in range(n):
            wl = inputs["center_wavelength_nm"] + (i - n//2) * spacing_nm
            channels.append(round(wl, 3))
        total_bw = inputs.get("bit_rate_gbps", 10) * n
        return json.dumps({
            "channel_wavelengths_nm": channels,
            "spacing_nm": round(spacing_nm, 4),
            "total_capacity_gbps": total_bw
        })

    elif name == "calculate_coherence_length":
        lc = (inputs["wavelength_nm"] * 1e-9)**2 / (inputs["spectral_width_nm"] * 1e-9)
        return json.dumps({
            "coherence_length_m": round(lc, 4),
            "coherence_length_mm": round(lc * 1000, 3)
        })

    elif name == "calculate_snr":
        snr = inputs["signal_power_dbm"] - inputs["noise_power_dbm"]
        return json.dumps({
            "SNR_db": round(snr, 2),
            "SNR_linear": round(10**(snr/10), 2)
        })

    elif name == "calculate_amplifier_gain":
        gain = inputs["output_power_dbm"] - inputs["input_power_dbm"]
        result = {"gain_db": round(gain, 2), "gain_linear": round(10**(gain/10), 2)}
        if "noise_figure_db" in inputs:
            result["noise_figure_db"] = inputs["noise_figure_db"]
        return json.dumps(result)

    elif name == "generate_report":
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/Users/mustafaabushagur/apra_report_{timestamp}.{inputs['format']}"
        with open(filename, "w") as f:
            f.write(f"# {inputs['title']}\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            f.write(inputs["content"])
        return json.dumps({"saved_to": filename, "status": "success"})

    return "Tool not found"

# Agentic loop
def run_apra(user_message, history):
    messages = history + [{"role": "user", "content": user_message}]
    client = anthropic.Anthropic(api_key=api_key)

    system = """You are APRA, the Autonomous Photonics Research Assistant for 
    Professor Mustafa Abushagur at RIT. You have access to 51 of his published 
    papers and 10 specialized photonics calculation tools. 

    When answering questions:
    1. Search his papers for relevant background
    2. Use calculation tools when numerical analysis is needed
    3. Combine paper knowledge with calculations for comprehensive answers
    4. Offer to generate a report for complex analyses

    Be thorough, technical, and always cite which papers you referenced."""

    steps = []

    while True:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            system=system,
            tools=tools,
            messages=messages
        )

        if response.stop_reason == "end_turn":
            final = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final = block.text
            return final, steps

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []

            for block in response.content:
                if block.type == "tool_use":
                    steps.append(f"🔧 Using tool: **{block.name}**")
                    result = execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result)
                    })

            messages.append({"role": "user", "content": tool_results})

# UI
with st.sidebar:
    st.header("APRA Tools")
    st.markdown("""
    **Available Tools (11):**
    - 🔍 Search 51 papers
    - 📊 Fiber loss calculator
    - 🔢 Numerical aperture
    - 📡 Dispersion analysis
    - ⚡ Power budget
    - 🌊 FBG wavelength shift
    - 📶 WDM channel planner
    - 🌊 Coherence length
    - 📈 SNR calculator
    - 🔊 Amplifier gain
    - 📄 Report generator
    """)
    st.markdown("---")
    if st.button("Clear conversation"):
        st.session_state.apra_messages = []
        st.rerun()

if "apra_messages" not in st.session_state:
    st.session_state.apra_messages = []

# Example prompts
st.markdown("### Try asking APRA:")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("*Design a 40km fiber link at 1550nm with 10Gbps*")
with col2:
    st.markdown("*What have I published about FBG sensors?*")
with col3:
    st.markdown("*Calculate WDM channels for 8 channel DWDM system*")

st.divider()

for msg in st.session_state.apra_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if question := st.chat_input("Ask APRA anything about photonics research or design..."):
    st.session_state.apra_messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("APRA is working..."):
            history = [{"role": m["role"], "content": m["content"]} 
                      for m in st.session_state.apra_messages[:-1]]
            answer, steps = run_apra(question, history)

            if steps:
                with st.expander("🔧 Tools used"):
                    for step in steps:
                        st.markdown(step)

            st.markdown(answer)
            st.session_state.apra_messages.append({
                "role": "assistant", 
                "content": answer
            })
