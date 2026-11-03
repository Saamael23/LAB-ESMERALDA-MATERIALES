import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ==========================================================
# EMERALD LAB | Berilo dopado con cromo (Cr3+)
# Modelo teórico simplificado basado en el notebook original.
# ==========================================================

st.set_page_config(
    page_title="EMERALD LAB | Berilo + Cr³⁺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- Estilo ----------
st.markdown("""
<style>
    .stApp { background: linear-gradient(180deg, #f5faf7 0%, #ffffff 45%); }
    .hero {
        background: linear-gradient(120deg, #073b2a, #138052);
        padding: 1.5rem 2rem; border-radius: 18px; color: white;
        margin-bottom: 1.2rem; box-shadow: 0 8px 24px rgba(7,59,42,.15);
    }
    .hero h1 { margin: 0; font-size: 2.2rem; letter-spacing: .04em; }
    .hero p { margin: .45rem 0 0 0; color: #e0f1e8; }
    .small-note { color: #64756c; font-size: .88rem; }
    div[data-testid="stMetric"] {
        background: #f2f8f4; border: 1px solid #dcebe1;
        padding: 12px 14px; border-radius: 12px;
    }
</style>
<div class="hero">
  <h1>EMERALD LAB</h1>
  <p>Laboratorio virtual de berilo dopado con cromo · estructura cristalina y propiedades ópticas</p>
</div>
""", unsafe_allow_html=True)

# ---------- Motor matemático: conserva el modelo del notebook ----------
WAVELENGTH = np.linspace(400, 700, 601)
C_REFERENCE = 0.5
L_REFERENCE = 5.0
LAMBDA_1, LAMBDA_2 = 430, 630
A1, A2 = 0.75, 0.68
SIGMA_1, SIGMA_2 = 28, 45

def gaussian(lam, center, sigma):
    return np.exp(-0.5 * ((lam - center) / sigma) ** 2)

def reference_absorbance(lam):
    return (
        A1 * gaussian(lam, LAMBDA_1, SIGMA_1)
        + A2 * gaussian(lam, LAMBDA_2, SIGMA_2)
    )

def calculate_absorbance(concentration, thickness):
    factor = (concentration / C_REFERENCE) * (thickness / L_REFERENCE)
    background = 0.01 * (thickness / L_REFERENCE)
    return background + factor * reference_absorbance(WAVELENGTH)

def calculate_transmittance(absorbance):
    return 10 ** (-absorbance)

def cie_gaussian(lam, center, left_width, right_width):
    sigma = np.where(lam < center, left_width, right_width)
    return np.exp(-0.5 * ((lam - center) / sigma) ** 2)

def cie_functions(lam):
    x = (
        1.056 * cie_gaussian(lam, 599.8, 37.9, 31.0)
        + 0.362 * cie_gaussian(lam, 442.0, 16.0, 26.7)
        - 0.065 * cie_gaussian(lam, 501.1, 20.4, 26.2)
    )
    y = (
        0.821 * cie_gaussian(lam, 568.8, 46.9, 40.5)
        + 0.286 * cie_gaussian(lam, 530.9, 16.3, 31.1)
    )
    z = (
        1.217 * cie_gaussian(lam, 437.0, 11.8, 36.0)
        + 0.681 * cie_gaussian(lam, 459.0, 26.0, 13.8)
    )
    return np.clip(x, 0, None), np.clip(y, 0, None), np.clip(z, 0, None)

def estimate_color(transmittance):
    x, y, z = cie_functions(WAVELENGTH)
    illuminant = np.ones_like(WAVELENGTH)

    X = np.trapezoid(illuminant * transmittance * x, WAVELENGTH)
    Y = np.trapezoid(illuminant * transmittance * y, WAVELENGTH)
    Z = np.trapezoid(illuminant * transmittance * z, WAVELENGTH)

    Xw = np.trapezoid(illuminant * x, WAVELENGTH)
    Yw = np.trapezoid(illuminant * y, WAVELENGTH)
    Zw = np.trapezoid(illuminant * z, WAVELENGTH)

    xyz = np.array([X / Xw, Y / Yw, Z / Zw])
    luminosity = float(np.clip(xyz[1], 0, 1))
    xyz_normalized = xyz / max(luminosity, 1e-10)

    matrix = np.array([
        [3.2406, -1.5372, -0.4986],
        [-0.9689, 1.8758, 0.0415],
        [0.0557, -0.2040, 1.0570]
    ])
    rgb_linear = np.clip(matrix @ xyz_normalized, 0, 1)
    rgb = np.where(
        rgb_linear <= 0.0031308,
        12.92 * rgb_linear,
        1.055 * rgb_linear ** (1 / 2.4) - 0.055
    )
    brightness = np.sqrt(luminosity)
    rgb_visual = np.clip(rgb * brightness, 0, 1)
    color_hex = "#{:02X}{:02X}{:02X}".format(
        *np.round(rgb_visual * 255).astype(int)
    )
    return color_hex, luminosity

def simulate(concentration, thickness):
    absorbance = calculate_absorbance(concentration, thickness)
    transmittance = calculate_transmittance(absorbance)
    color, luminosity = estimate_color(transmittance)
    return {
        "absorbance": absorbance,
        "transmittance": transmittance,
        "color": color,
        "luminosity": luminosity
    }

# ---------- Modelo 3D esquemático del notebook ----------
def build_crystal_figure(concentration):
    fig = go.Figure()
    atomic_colors = {
        "Si": "#F0B52B", "O": "#E64B4B", "Al": "#3478C8",
        "Be": "#A66BE0", "Cr": "#168B4F"
    }

    def add_atoms(name, positions, color, size):
        if not positions:
            return
        points = np.asarray(positions)
        fig.add_trace(go.Scatter3d(
            x=points[:, 0], y=points[:, 1], z=points[:, 2],
            mode="markers", name=name,
            marker=dict(size=size, color=color, opacity=0.95,
                        line=dict(color="white", width=0.5)),
            hovertemplate=name + "<br>x: %{x:.2f}<br>y: %{y:.2f}<br>z: %{z:.2f}<extra></extra>"
        ))

    si_positions, oxygen_positions = [], []
    radius = 2.0
    for z_center in [-1.0, 1.0]:
        for i in range(6):
            angle = 2 * np.pi * i / 6
            x, y = radius * np.cos(angle), radius * np.sin(angle)
            si_positions.append([x, y, z_center])
            for j in range(3):
                displacement = 0.38 if j == 0 else 0.65
                oxygen_angle = angle + (j - 1) * 0.27
                xo = x + displacement * np.cos(oxygen_angle)
                yo = y + displacement * np.sin(oxygen_angle)
                zo = z_center + (0.20 if j == 1 else -0.20)
                oxygen_positions.append([xo, yo, zo])

    add_atoms("Silicio (Si⁴⁺)", si_positions, atomic_colors["Si"], 8)
    add_atoms("Oxígeno (O²⁻)", oxygen_positions, atomic_colors["O"], 5)

    aluminum_positions = [
        [x, y, 0] for x in [-0.9, 0.9] for y in [-0.9, 0.9]
    ]
    beryllium_positions = [
        [-1.2, 0, 0.8], [1.2, 0, -0.8],
        [0, -1.2, 0.8], [0, 1.2, -0.8]
    ]

    # Amplificación visual didáctica: no representa ocupación real.
    chromium_count = min(4, int(round(concentration * 4)))
    chromium_positions = aluminum_positions[:chromium_count]
    remaining_aluminum = aluminum_positions[chromium_count:]

    add_atoms("Aluminio (Al³⁺)", remaining_aluminum, atomic_colors["Al"], 12)
    add_atoms("Cromo (Cr³⁺)", chromium_positions, atomic_colors["Cr"], 15)
    add_atoms("Berilio (Be²⁺)", beryllium_positions, atomic_colors["Be"], 9)

    angles = np.linspace(0, 2 * np.pi, 7)
    hx, hy = 3.0 * np.cos(angles), 3.0 * np.sin(angles)
    for z in [-2.0, 2.0]:
        fig.add_trace(go.Scatter3d(
            x=hx, y=hy, z=np.full(7, z), mode="lines",
            line=dict(color="#48A47A", width=4),
            showlegend=False, hoverinfo="skip"
        ))
    for i in range(6):
        fig.add_trace(go.Scatter3d(
            x=[hx[i], hx[i]], y=[hy[i], hy[i]], z=[-2, 2],
            mode="lines", line=dict(color="#48A47A", width=3),
            showlegend=False, hoverinfo="skip"
        ))

    fig.update_layout(
        title="Estructura tridimensional esquemática del berilo",
        height=610,
        margin=dict(l=0, r=0, b=0, t=55),
        legend=dict(orientation="h", y=-0.08),
        scene=dict(
            xaxis=dict(visible=False), yaxis=dict(visible=False),
            zaxis=dict(visible=False), aspectmode="data",
            camera=dict(eye=dict(x=1.7, y=1.7, z=1.2))
        )
    )
    return fig

# ---------- Experimento óptico ----------
def wavelength_color(lam):
    if lam < 450: return "#6633CC"
    if lam < 490: return "#2459DB"
    if lam < 520: return "#00A6B4"
    if lam < 565: return "#20A34A"
    if lam < 590: return "#B5AD20"
    if lam < 625: return "#E18A25"
    return "#C83C3C"

def build_optical_figure(transmittance):
    fig = make_subplots(
        rows=2, cols=1, vertical_spacing=0.16,
        row_heights=[0.42, 0.58],
        subplot_titles=("Interacción de la luz con el cristal",
                        "Espectro de luz incidente y transmitida")
    )

    # Esquema conceptual de cristal y rayos.
    crystal_x = [4, 4.7, 7.3, 8, 7.3, 4.7, 4]
    crystal_y = [0.5, 1.7, 1.7, 0.5, -0.5, -0.5, 0.5]
    fig.add_trace(go.Scatter(
        x=crystal_x, y=crystal_y, fill="toself",
        fillcolor="rgba(22,139,79,0.28)",
        line=dict(color="#0C5131", width=2),
        name="Cristal", hoverinfo="skip"
    ), row=1, col=1)
    fig.add_annotation(
        x=6, y=1.95, text="<b>BERILO DOPADO CON Cr³⁺</b>",
        showarrow=False, font=dict(color="#14764D"), row=1, col=1
    )
    fig.add_annotation(
        x=3.8, y=0, ax=0.5, ay=0, xref="x", yref="y",
        axref="x", ayref="y", text="",
        showarrow=True, arrowhead=3, arrowsize=1.3,
        arrowwidth=5, arrowcolor="#D9A323", row=1, col=1
    )
    fig.add_annotation(
        x=1.8, y=0.28, text="LUZ BLANCA INCIDENTE",
        showarrow=False, font=dict(size=11), row=1, col=1
    )

    representative_wavelengths = [430, 530, 630]
    labels = ["Azul-violeta", "Verde", "Rojo"]
    heights = [0.30, 0.0, -0.30]
    for lam, label, y in zip(representative_wavelengths, labels, heights):
        idx = int(np.argmin(np.abs(WAVELENGTH - lam)))
        transmission = float(transmittance[idx])
        color = wavelength_color(lam)
        fig.add_trace(go.Scatter(
            x=[4.1, 7.8, 10], y=[y, y, y],
            mode="lines+markers",
            line=dict(color=color, width=3, dash="dash"),
            marker=dict(size=[0, 0, 8], color=color),
            opacity=max(0.08, transmission),
            name=f"{label}: {transmission*100:.1f}%",
            showlegend=True
        ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=WAVELENGTH, y=np.ones_like(WAVELENGTH) * 100,
        mode="lines", line=dict(color="#777777", dash="dash", width=2),
        name="Luz incidente (100 %)"
    ), row=2, col=1)
    fig.add_trace(go.Scatter(
        x=WAVELENGTH, y=transmittance * 100,
        mode="lines", line=dict(color="#168B4F", width=3),
        fill="tozeroy", fillcolor="rgba(22,139,79,0.13)",
        name="Luz transmitida"
    ), row=2, col=1)
    for lam in representative_wavelengths:
        idx = int(np.argmin(np.abs(WAVELENGTH - lam)))
        fig.add_trace(go.Scatter(
            x=[lam], y=[transmittance[idx] * 100], mode="markers",
            marker=dict(size=10, color=wavelength_color(lam)),
            showlegend=False, hovertemplate=f"{lam} nm: %{{y:.2f}} %<extra></extra>"
        ), row=2, col=1)

    fig.update_xaxes(title_text="Esquema conceptual", range=[0, 12], row=1, col=1)
    fig.update_yaxes(range=[-1.2, 2.4], visible=False, row=1, col=1)
    fig.update_xaxes(title_text="Longitud de onda (nm)", range=[400, 700], row=2, col=1)
    fig.update_yaxes(title_text="Intensidad relativa (%)", range=[0, 110], row=2, col=1)
    fig.update_layout(
        height=790, margin=dict(l=20, r=20, t=75, b=20),
        legend=dict(orientation="h", y=-0.12)
    )
    return fig

# ---------- Controles ----------
with st.sidebar:
    st.markdown("## Parámetros del experimento")
    if "concentration" not in st.session_state:
        st.session_state.concentration = 0.5
    if "thickness" not in st.session_state:
        st.session_state.thickness = 5

    st.caption("Escenarios predefinidos")
    b1, b2 = st.columns(2)
    if b1.button("Sin dopaje", use_container_width=True):
        st.session_state.concentration, st.session_state.thickness = 0.0, 5
    if b2.button("Referencia", use_container_width=True):
        st.session_state.concentration, st.session_state.thickness = 0.5, 5
    b3, b4 = st.columns(2)
    if b3.button("Alto dopaje", use_container_width=True):
        st.session_state.concentration, st.session_state.thickness = 1.0, 5
    if b4.button("Mayor espesor", use_container_width=True):
        st.session_state.concentration, st.session_state.thickness = 0.5, 10

    concentration = st.slider(
        "Concentración relativa de Cr³⁺ (%)",
        min_value=0.0, max_value=1.0, step=0.05,
        key="concentration"
    )
    thickness = st.slider(
        "Espesor del cristal (mm)",
        min_value=1, max_value=10, step=1,
        key="thickness"
    )
    st.divider()
    st.caption("Los controles actualizan simultáneamente las gráficas, el color estimado y la representación 3D.")

result = simulate(concentration, thickness)
absorbance = result["absorbance"]
transmittance = result["transmittance"]
color_hex = result["color"]
luminosity = result["luminosity"]

# ---------- Navegación ----------
tab_lab, tab_structure, tab_light, tab_about = st.tabs([
    "Laboratorio óptico", "Estructura 3D", "Experimento de luz", "Modelo y alcance"
])

with tab_lab:
    st.subheader("Resultados del experimento")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Absorbancia máxima", f"{np.max(absorbance):.4f}")
    c2.metric("Transmitancia promedio", f"{np.mean(transmittance)*100:.2f} %")
    green_mask = (WAVELENGTH >= 500) & (WAVELENGTH <= 570)
    green_transmission = float(np.mean(transmittance[green_mask]) * 100)
    c3.metric("Transmisión región verde", f"{green_transmission:.2f} %")
    c4.metric("Luminosidad relativa", f"{luminosity*100:.2f} %")

    color_col, info_col = st.columns([1, 2])
    with color_col:
        st.markdown("**Color estimado del cristal**")
        st.markdown(
            f'<div style="height:95px;border-radius:14px;background:{color_hex};'
            f'border:1px solid #cbd5ce;"></div>'
            f'<p style="text-align:center;font-weight:600">{color_hex}</p>',
            unsafe_allow_html=True
        )
    with info_col:
        st.markdown("**Parámetros actuales**")
        st.write(f"- Concentración relativa de Cr³⁺: **{concentration:.2f} %**")
        st.write(f"- Espesor: **{thickness} mm**")
        st.write("- Transmitancia calculada mediante la relación de Beer-Lambert simplificada.")

    spectra = go.Figure()
    spectra.add_trace(go.Scatter(
        x=WAVELENGTH, y=absorbance, mode="lines",
        line=dict(color="#B34D55", width=3), name="Absorbancia"
    ))
    spectra.update_layout(
        title="Espectro de absorbancia", xaxis_title="Longitud de onda (nm)",
        yaxis_title="Absorbancia (u.a.)", height=360,
        margin=dict(l=15, r=15, t=55, b=15)
    )
    trans_fig = go.Figure()
    trans_fig.add_trace(go.Scatter(
        x=WAVELENGTH, y=transmittance*100, mode="lines",
        line=dict(color="#188D57", width=3), fill="tozeroy",
        fillcolor="rgba(24,141,87,0.13)", name="Transmitancia"
    ))
    trans_fig.update_layout(
        title="Espectro de transmitancia", xaxis_title="Longitud de onda (nm)",
        yaxis_title="Transmitancia (%)", yaxis=dict(range=[0, 105]),
        height=360, margin=dict(l=15, r=15, t=55, b=15)
    )
    g1, g2 = st.columns(2)
    with g1: st.plotly_chart(spectra, use_container_width=True)
    with g2: st.plotly_chart(trans_fig, use_container_width=True)

    if concentration == 0:
        st.info("En este escenario no hay dopaje de cromo en el modelo.")
    elif green_transmission > np.mean(transmittance)*100:
        st.success("La región verde presenta una transmisión promedio superior al promedio del espectro.")
    else:
        st.info("La absorción modifica la transmisión del espectro visible.")
    st.caption("Resultados de un modelo teórico simplificado; no corresponden a mediciones experimentales.")

with tab_structure:
    st.subheader("Representación tridimensional del berilo")
    st.plotly_chart(build_crystal_figure(concentration), use_container_width=True)
    dot = '<span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:{c};margin-right:5px;vertical-align:middle;"></span>'
    legend = " &nbsp;·&nbsp; ".join(
        dot.format(c=c) + n for n, c in [
            ("Si", "#F0B52B"), ("O", "#E64B4B"), ("Al", "#3478C8"),
            ("Be", "#A66BE0"), ("Cr", "#168B4F")
        ]
    )
    st.markdown(f"**Código de colores:** {legend}", unsafe_allow_html=True)
    st.markdown("""
    La representación es esquemática y sirve para visualizar la sustitución conceptual de Al³⁺ por Cr³⁺.
    El número de sitios de cromo se amplifica visualmente para que el cambio pueda apreciarse; no representa
    una ocupación cristalográfica real ni una estructura refinada a partir de un archivo CIF.
    """)

with tab_light:
    st.subheader("Interacción de la luz con el cristal")
    st.plotly_chart(build_optical_figure(transmittance), use_container_width=True)
    st.markdown("**Transmisión en longitudes de onda representativas**")
    cols = st.columns(3)
    for col, lam, label in zip(cols, [430, 530, 630], ["Azul-violeta", "Verde", "Rojo"]):
        idx = int(np.argmin(np.abs(WAVELENGTH - lam)))
        col.metric(f"{label} ({lam} nm)", f"{transmittance[idx]*100:.2f} %")

with tab_about:
    st.subheader("Sobre el modelo")
    st.markdown("""
    Esta aplicación traslada el modelo del notebook original a una interfaz web interactiva.

    - **Absorbancia:** se representa mediante dos bandas gaussianas centradas en 430 y 630 nm.
    - **Concentración y espesor:** escalan la absorbancia de referencia mediante una relación de Beer-Lambert simplificada.
    - **Transmitancia:** se calcula mediante la expresión T(λ) = 10^(-A(λ)).
    - **Color:** se estima mediante una aproximación analítica de funciones colorimétricas CIE 1931 y una conversión XYZ–sRGB.
    - **Estructura 3D:** es un esquema didáctico, no una reconstrucción cristalográfica exacta.
    """)

    st.warning(
        "Importante: el espectro de absorbancia, la transmitancia y el color son resultados de un modelo teórico "
        "simplificado. No deben presentarse como datos experimentales ni como una predicción cuantitativa "
        "validada para una muestra real de esmeralda."
    )

st.markdown("---")
st.markdown(
    '<p class="small-note">EMERALD LAB · Recurso didáctico para Fundamentos de los Materiales.</p>',
    unsafe_allow_html=True
)
