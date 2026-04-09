
import streamlit as st
import anthropic
import os
import math

st.set_page_config(page_title="Optical Design Advisor", page_icon="🔭", layout="wide")
st.title("🔭 Optical Design Advisor")
st.markdown("*Fiber Optic System Design Tool — Prof. Mustafa A.G. Abushagur, RIT*")
st.divider()

# Clean API key
api_key = os.environ.get("ANTHROPIC_API_KEY", "").replace(" ", "")

# Sidebar
with st.sidebar:
    st.header("Design Tools")
    tool = st.selectbox("Select Calculator:", [
        "System Overview",
        "Fiber Loss Calculator",
        "Power Budget Calculator",
        "Dispersion Analysis",
        "Numerical Aperture",
        "Cutoff Wavelength",
        "Splice & Connector Loss",
        "Receiver Sensitivity",
        "System Margin",
        "Coherence Length",
    ])
    st.markdown("---")
    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.rerun()

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Tool panels
st.subheader(f"📐 {tool}")

if tool == "Fiber Loss Calculator":
    col1, col2 = st.columns(2)
    with col1:
        length = st.number_input("Fiber Length (km)", value=10.0, step=0.5)
        attenuation = st.number_input("Attenuation Coefficient (dB/km)", value=0.2, step=0.01)
        num_splices = st.number_input("Number of Splices", value=2, step=1)
        splice_loss = st.number_input("Loss per Splice (dB)", value=0.1, step=0.01)
    with col2:
        num_connectors = st.number_input("Number of Connectors", value=2, step=1)
        connector_loss = st.number_input("Loss per Connector (dB)", value=0.5, step=0.01)

    if st.button("Calculate Total Loss"):
        fiber_loss = length * attenuation
        total_splice = num_splices * splice_loss
        total_connector = num_connectors * connector_loss
        total = fiber_loss + total_splice + total_connector

        st.markdown("### Results")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Fiber Loss", f"{fiber_loss:.2f} dB")
        col2.metric("Splice Loss", f"{total_splice:.2f} dB")
        col3.metric("Connector Loss", f"{total_connector:.2f} dB")
        col4.metric("Total Loss", f"{total:.2f} dB")

elif tool == "Power Budget Calculator":
    col1, col2 = st.columns(2)
    with col1:
        tx_power = st.number_input("Transmitter Power (dBm)", value=0.0, step=0.5)
        rx_sensitivity = st.number_input("Receiver Sensitivity (dBm)", value=-30.0, step=0.5)
        total_loss = st.number_input("Total System Loss (dB)", value=15.0, step=0.5)
    with col2:
        safety_margin = st.number_input("Safety Margin (dB)", value=3.0, step=0.5)

    if st.button("Calculate Power Budget"):
        available_power = tx_power - rx_sensitivity
        required_power = total_loss + safety_margin
        margin = available_power - required_power

        st.markdown("### Results")
        col1, col2, col3 = st.columns(3)
        col1.metric("Available Power", f"{available_power:.2f} dB")
        col2.metric("Required Power", f"{required_power:.2f} dB")
        col3.metric("System Margin", f"{margin:.2f} dB",
                   delta="OK" if margin > 0 else "FAIL")

        if margin > 0:
            st.success(f"✓ System viable with {margin:.2f} dB margin")
        else:
            st.error(f"✗ System fails by {abs(margin):.2f} dB")

elif tool == "Dispersion Analysis":
    col1, col2 = st.columns(2)
    with col1:
        wavelength = st.number_input("Wavelength (nm)", value=1550.0, step=1.0)
        dispersion = st.number_input("Dispersion Coefficient (ps/nm/km)", value=17.0, step=0.5)
        length_km = st.number_input("Fiber Length (km)", value=10.0, step=0.5)
    with col2:
        source_width = st.number_input("Source Spectral Width (nm)", value=0.1, step=0.01)
        bit_rate = st.number_input("Bit Rate (Gbps)", value=10.0, step=1.0)

    if st.button("Analyze Dispersion"):
        pulse_broadening = abs(dispersion) * source_width * length_km
        max_length = 1 / (bit_rate * abs(dispersion) * source_width) * 1000

        st.markdown("### Results")
        col1, col2 = st.columns(2)
        col1.metric("Pulse Broadening", f"{pulse_broadening:.3f} ps")
        col2.metric("Max Dispersion-Limited Length", f"{max_length:.2f} km")

elif tool == "Numerical Aperture":
    col1, col2 = st.columns(2)
    with col1:
        n_core = st.number_input("Core Refractive Index (n1)", value=1.468, step=0.001, format="%.3f")
        n_clad = st.number_input("Cladding Refractive Index (n2)", value=1.450, step=0.001, format="%.3f")
    with col2:
        core_diameter = st.number_input("Core Diameter (μm)", value=50.0, step=1.0)
        wavelength_na = st.number_input("Wavelength (μm)", value=1.55, step=0.01)

    if st.button("Calculate NA"):
        NA = math.sqrt(n_core**2 - n_clad**2)
        acceptance_angle = math.degrees(math.asin(NA))
        delta = (n_core - n_clad) / n_core
        V_number = (math.pi * core_diameter * NA) / wavelength_na

        st.markdown("### Results")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Numerical Aperture", f"{NA:.4f}")
        col2.metric("Acceptance Angle", f"{acceptance_angle:.2f}°")
        col3.metric("Relative Index Δ", f"{delta:.4f}")
        col4.metric("V-Number", f"{V_number:.3f}")

        if V_number < 2.405:
            st.success("✓ Single-mode operation")
        else:
            st.warning(f"⚠ Multimode operation ({int(V_number**2/2)} modes approx.)")

elif tool == "Cutoff Wavelength":
    col1, col2 = st.columns(2)
    with col1:
        n1 = st.number_input("Core Index", value=1.468, step=0.001, format="%.3f")
        n2 = st.number_input("Cladding Index", value=1.450, step=0.001, format="%.3f")
        diameter = st.number_input("Core Diameter (μm)", value=8.0, step=0.5)

    if st.button("Calculate Cutoff Wavelength"):
        NA_c = math.sqrt(n1**2 - n2**2)
        lambda_cutoff = (math.pi * diameter * NA_c) / 2.405

        st.markdown("### Results")
        col1, col2 = st.columns(2)
        col1.metric("Cutoff Wavelength", f"{lambda_cutoff:.3f} μm")
        col2.metric("NA", f"{NA_c:.4f}")

        if lambda_cutoff < 1.31:
            st.success("✓ Single-mode at 1310nm and 1550nm")
        elif lambda_cutoff < 1.55:
            st.warning("⚠ Single-mode only at 1550nm")
        else:
            st.error("✗ Multimode at both windows")

elif tool == "Splice & Connector Loss":
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Splice Loss")
        offset = st.number_input("Lateral Offset (μm)", value=1.0, step=0.1)
        core_d = st.number_input("Core Diameter (μm)", value=50.0, step=1.0)
        angular = st.number_input("Angular Misalignment (degrees)", value=0.5, step=0.1)
    with col2:
        st.subheader("Connector Loss")
        n_conn = st.number_input("Refractive Index", value=1.468, step=0.001, format="%.3f")
        gap = st.number_input("Air Gap (μm)", value=0.0, step=0.1)

    if st.button("Calculate Losses"):
        offset_loss = -10 * math.log10(1 - (offset / core_d)**2) if offset < core_d else 99
        angular_loss = -10 * math.log10(1 - (angular * math.pi / 180)**2)
        fresnel_loss = -10 * math.log10((2 * n_conn / (1 + n_conn))**2) if gap > 0 else 0

        st.markdown("### Results")
        col1, col2, col3 = st.columns(3)
        col1.metric("Offset Loss", f"{offset_loss:.3f} dB")
        col2.metric("Angular Loss", f"{angular_loss:.3f} dB")
        col3.metric("Fresnel Loss", f"{fresnel_loss:.3f} dB")

elif tool == "Receiver Sensitivity":
    col1, col2 = st.columns(2)
    with col1:
        bit_rate_r = st.number_input("Bit Rate (Gbps)", value=10.0, step=1.0)
        ber = st.selectbox("Target BER", ["1e-9", "1e-12", "1e-15"])
        wavelength_r = st.number_input("Wavelength (nm)", value=1550.0, step=1.0)
    with col2:
        responsivity = st.number_input("Detector Responsivity (A/W)", value=0.8, step=0.05)

    if st.button("Calculate Sensitivity"):
        ber_factors = {"1e-9": 12.0, "1e-12": 14.1, "1e-15": 16.0}
        Q = ber_factors[ber]
        h = 6.626e-34
        c = 3e8
        photon_energy = h * c / (wavelength_r * 1e-9)
        min_photons = Q**2 / 2
        min_power_w = min_photons * photon_energy * bit_rate_r * 1e9
        min_power_dbm = 10 * math.log10(min_power_w / 1e-3)

        st.markdown("### Results")
        col1, col2 = st.columns(2)
        col1.metric("Minimum Power", f"{min_power_dbm:.1f} dBm")
        col2.metric("Q Factor", f"{Q}")

elif tool == "System Margin":
    col1, col2 = st.columns(2)
    with col1:
        tx_p = st.number_input("TX Power (dBm)", value=3.0, step=0.5)
        rx_sens = st.number_input("RX Sensitivity (dBm)", value=-28.0, step=0.5)
        fiber_l = st.number_input("Fiber Loss (dB)", value=10.0, step=0.5)
    with col2:
        splice_l = st.number_input("Splice Loss (dB)", value=1.0, step=0.1)
        connector_l = st.number_input("Connector Loss (dB)", value=1.0, step=0.1)
        aging = st.number_input("Aging Margin (dB)", value=2.0, step=0.5)

    if st.button("Calculate System Margin"):
        total_l = fiber_l + splice_l + connector_l + aging
        margin = tx_p - rx_sens - total_l

        st.markdown("### Results")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Loss", f"{total_l:.2f} dB")
        col2.metric("Link Budget", f"{tx_p - rx_sens:.2f} dB")
        col3.metric("System Margin", f"{margin:.2f} dB",
                   delta="PASS" if margin > 0 else "FAIL")

elif tool == "Coherence Length":
    col1, col2 = st.columns(2)
    with col1:
        wavelength_c = st.number_input("Wavelength (nm)", value=1550.0, step=1.0)
        delta_lambda = st.number_input("Spectral Width Δλ (nm)", value=0.1, step=0.01)

    if st.button("Calculate Coherence Length"):
        lc = (wavelength_c * 1e-9)**2 / (delta_lambda * 1e-9)
        lc_mm = lc * 1000

        st.markdown("### Results")
        col1, col2 = st.columns(2)
        col1.metric("Coherence Length", f"{lc:.4f} m")
        col2.metric("Coherence Length", f"{lc_mm:.2f} mm")

else:
    st.markdown("""
    ### Welcome to the Optical Design Advisor

    Select a calculator from the sidebar to get started.

    **Available Tools:**
    - 📊 **Fiber Loss Calculator** — Total link loss analysis
    - ⚡ **Power Budget Calculator** — System viability check  
    - 📡 **Dispersion Analysis** — Pulse broadening calculation
    - 🔢 **Numerical Aperture** — NA, acceptance angle, V-number
    - ✂️ **Cutoff Wavelength** — Single/multimode determination
    - 🔗 **Splice & Connector Loss** — Mechanical loss analysis
    - 📡 **Receiver Sensitivity** — Minimum detectable power
    - 📈 **System Margin** — End-to-end margin calculation
    - 🌊 **Coherence Length** — Source coherence analysis

    ---
    **Ask the AI advisor any fiber optic design question below:**
    """)

st.divider()

# AI Chat section
st.subheader("💬 Ask the AI Design Advisor")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if question := st.chat_input("Ask a fiber optic design question..."):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                system="""You are an expert fiber optic system design advisor working with 
                Professor Mustafa Abushagur at RIT. Answer technical questions about fiber 
                optic system design, calculations, and best practices. Be precise and technical.
                Include relevant equations when helpful.""",
                messages=[{"role": "user", "content": question}]
            )
            answer = message.content[0].text
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
