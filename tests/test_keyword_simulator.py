"""Tests for KeywordSimulator."""
import pytest
from pulso.engine.keyword_simulator import KeywordSimulator
from pulso.models.schemas import WorldState, Emotion


@pytest.fixture
def sim():
    return KeywordSimulator()


class TestKeywordMatch:
    def test_dollar_triggers_anger(self, sim):
        ws = sim.simulate("sube el dólar a 22 pesos")
        # Epicenter states should be anger
        cdmx = next(s for s in ws.states if s.state_code == "CDMX")
        assert cdmx.emotion == Emotion.ANGER

    def test_dollar_border_states_get_joy(self, sim):
        ws = sim.simulate("el dólar sube mucho")
        # BC is a joy_state for dollar rule
        bc = next(s for s in ws.states if s.state_code == "BC")
        assert bc.emotion == Emotion.JOY

    def test_sismo_triggers_fear(self, sim):
        ws = sim.simulate("se registró un sismo en la Ciudad de México")
        cdmx = next(s for s in ws.states if s.state_code == "CDMX")
        assert cdmx.emotion == Emotion.FEAR
        assert cdmx.intensity >= 0.90

    def test_futbol_triggers_joy_everywhere(self, sim):
        ws = sim.simulate("gol de la selección en el mundial")
        joy_count = sum(1 for s in ws.states if s.emotion == Emotion.JOY)
        # Joy dominant (≥18 states) with regional diversity for the rest
        assert joy_count >= 18
        emotions = {s.emotion for s in ws.states}
        assert len(emotions) >= 2

    def test_navidad_triggers_joy(self, sim):
        ws = sim.simulate("se acerca la navidad y la celebración")
        joy_count = sum(1 for s in ws.states if s.emotion == Emotion.JOY)
        # Joy dominant with some regional variation
        assert joy_count >= 18

    def test_unknown_event_uses_default(self, sim):
        ws = sim.simulate("hola mundo como estas")
        # Default rule — CDMX gets fear at 0.50
        cdmx = next(s for s in ws.states if s.state_code == "CDMX")
        assert cdmx.emotion == Emotion.FEAR
        assert cdmx.intensity == pytest.approx(0.50, abs=0.01)

    def test_secuestro_triggers_sadness_in_epicenter(self, sim):
        ws = sim.simulate("ola de secuestros y violencia en el norte")
        chih = next(s for s in ws.states if s.state_code == "CHIH")
        assert chih.emotion == Emotion.SADNESS

    def test_inversion_triggers_hope(self, sim):
        ws = sim.simulate("gran inversión extranjera impulsa el crecimiento")
        cdmx = next(s for s in ws.states if s.state_code == "CDMX")
        assert cdmx.emotion == Emotion.HOPE


class TestWorldStateStructure:
    def test_returns_32_states(self, sim):
        ws = sim.simulate("el dólar sube a 22 pesos")
        assert len(ws.states) == 32

    def test_all_states_have_valid_intensity(self, sim):
        ws = sim.simulate("el dólar sube a 22 pesos")
        for s in ws.states:
            assert 0.0 <= s.intensity <= 1.0

    def test_wave_order_in_range(self, sim):
        ws = sim.simulate("el dólar sube a 22 pesos")
        for s in ws.states:
            assert 0 <= s.wave_order <= 5

    def test_spread_matrix_has_all_states(self, sim):
        ws = sim.simulate("sismo en la ciudad")
        assert len(ws.spread_matrix) == 32

    def test_event_source_is_keyword(self, sim):
        ws = sim.simulate("el dólar sube a 22 pesos")
        assert ws.event_source == "keyword"

    def test_event_text_preserved(self, sim):
        text = "el dólar sube a 22 pesos"
        ws = sim.simulate(text)
        assert ws.event_text == text

    def test_metadata_has_method(self, sim):
        ws = sim.simulate("el dólar sube a 22 pesos")
        assert ws.metadata.get("method") == "keyword"


class TestWaveOrder:
    def test_cdmx_origin_has_zero_order(self, sim):
        ws = sim.simulate("el dólar sube mucho")
        cdmx = next(s for s in ws.states if s.state_code == "CDMX")
        assert cdmx.wave_order == 0

    def test_neighbor_has_lower_order_than_distant(self, sim):
        ws = sim.simulate("el sismo fue en oaxaca fuerte")
        # OAX is epicenter, GRO should be closer than BC
        gro = next(s for s in ws.states if s.state_code == "GRO")
        bc = next(s for s in ws.states if s.state_code == "BC")
        assert gro.wave_order < bc.wave_order


# ── Expanded keyword coverage (28-rule dictionary) ────────────────────────────

class TestExpandedKeywords:
    """Tests for each major category added in the expanded EVENT_RULES."""

    # Sports — joy
    def test_mundial_triggers_joy(self, sim):
        ws = sim.simulate("mexico gana el mundial")
        cdmx = next(s for s in ws.states if s.state_code == "CDMX")
        assert cdmx.emotion == Emotion.JOY

    def test_seleccion_alone_triggers_joy(self, sim):
        ws = sim.simulate("la seleccion juega hoy")
        cdmx = next(s for s in ws.states if s.state_code == "CDMX")
        assert cdmx.emotion == Emotion.JOY

    def test_liga_mx_triggers_joy(self, sim):
        ws = sim.simulate("gran partido de liga mx esta noche")
        cdmx = next(s for s in ws.states if s.state_code == "CDMX")
        assert cdmx.emotion == Emotion.JOY

    def test_canelo_triggers_joy(self, sim):
        ws = sim.simulate("canelo gano el campeonato mundial de box")
        cdmx = next(s for s in ws.states if s.state_code == "CDMX")
        assert cdmx.emotion == Emotion.JOY

    # Sports — defeat / sadness
    def test_seleccion_eliminada_triggers_sadness(self, sim):
        # Avoids "mundial" (joy keyword) — tests defeat context alone
        ws = sim.simulate("seleccion eliminada en cuartos de final")
        cdmx = next(s for s in ws.states if s.state_code == "CDMX")
        assert cdmx.emotion == Emotion.SADNESS

    def test_eliminados_triggers_sadness(self, sim):
        ws = sim.simulate("los mexicanos quedamos eliminados en cuartos")
        cdmx = next(s for s in ws.states if s.state_code == "CDMX")
        assert cdmx.emotion == Emotion.SADNESS

    def test_adios_mundial_triggers_sadness(self, sim):
        ws = sim.simulate("adios mundial mexico pierde contra argentina")
        cdmx = next(s for s in ws.states if s.state_code == "CDMX")
        assert cdmx.emotion == Emotion.SADNESS

    # Economy — anger
    def test_dolar_triggers_anger(self, sim):
        ws = sim.simulate("sube el dolar a 25 pesos")
        cdmx = next(s for s in ws.states if s.state_code == "CDMX")
        assert cdmx.emotion == Emotion.ANGER

    def test_inflacion_triggers_anger(self, sim):
        ws = sim.simulate("la inflacion sigue subiendo y todo esta caro")
        cdmx = next(s for s in ws.states if s.state_code == "CDMX")
        assert cdmx.emotion == Emotion.ANGER

    def test_gasolinazo_triggers_anger(self, sim):
        ws = sim.simulate("gasolinazo otra vez sube la gasolina")
        cdmx = next(s for s in ws.states if s.state_code == "CDMX")
        assert cdmx.emotion == Emotion.ANGER

    # Economy — hope
    def test_nearshoring_triggers_hope(self, sim):
        ws = sim.simulate("nearshoring en queretaro trae miles de empleos")
        cdmx = next(s for s in ws.states if s.state_code == "CDMX")
        assert cdmx.emotion == Emotion.HOPE

    def test_salario_minimo_triggers_hope(self, sim):
        ws = sim.simulate("aumenta el salario minimo en mexico")
        cdmx = next(s for s in ws.states if s.state_code == "CDMX")
        assert cdmx.emotion == Emotion.HOPE

    # Natural disasters — fear
    def test_temblor_triggers_fear(self, sim):
        ws = sim.simulate("temblor de 7 grados en oaxaca")
        cdmx = next(s for s in ws.states if s.state_code == "CDMX")
        assert cdmx.emotion == Emotion.FEAR

    def test_popocatepetl_triggers_fear(self, sim):
        ws = sim.simulate("erupcion del popocatepetl lanza ceniza")
        pue = next(s for s in ws.states if s.state_code == "PUE")
        assert pue.emotion == Emotion.FEAR

    def test_huracan_triggers_fear(self, sim):
        ws = sim.simulate("huracan categoria 5 se acerca al pacifico")
        cdmx = next(s for s in ws.states if s.state_code == "CDMX")
        assert cdmx.emotion == Emotion.FEAR

    def test_inundacion_triggers_fear(self, sim):
        ws = sim.simulate("inundacion grave en tabasco colonias afectadas")
        cdmx = next(s for s in ws.states if s.state_code == "CDMX")
        assert cdmx.emotion == Emotion.FEAR

    def test_sequia_triggers_fear(self, sim):
        ws = sim.simulate("sequia historica en el norte dia cero en monterrey")
        nl = next(s for s in ws.states if s.state_code == "NL")
        assert nl.emotion == Emotion.FEAR

    # Crime — sadness
    def test_balacera_triggers_sadness(self, sim):
        ws = sim.simulate("balacera en sinaloa deja varios muertos")
        sin = next(s for s in ws.states if s.state_code == "SIN")
        assert sin.emotion == Emotion.SADNESS

    def test_feminicidio_triggers_sadness(self, sim):
        ws = sim.simulate("feminicidio en el estado de mexico indignacion nacional")
        chih = next(s for s in ws.states if s.state_code == "CHIH")
        assert chih.emotion == Emotion.SADNESS

    def test_narco_triggers_sadness(self, sim):
        ws = sim.simulate("narco enfrenta al ejercito en la frontera")
        chih = next(s for s in ws.states if s.state_code == "CHIH")
        assert chih.emotion == Emotion.SADNESS

    # Culture / celebration — joy
    def test_dia_de_muertos_triggers_joy(self, sim):
        ws = sim.simulate("dia de muertos en oaxaca es patrimonio mundial")
        oax = next(s for s in ws.states if s.state_code == "OAX")
        assert oax.emotion == Emotion.JOY

    def test_posadas_triggers_joy(self, sim):
        ws = sim.simulate("llegan las posadas y la navidad en mexico")
        cdmx = next(s for s in ws.states if s.state_code == "CDMX")
        assert cdmx.emotion == Emotion.JOY

    # Health — fear
    def test_pandemia_triggers_fear(self, sim):
        ws = sim.simulate("nueva pandemia de virus se extiende por mexico")
        cdmx = next(s for s in ws.states if s.state_code == "CDMX")
        assert cdmx.emotion == Emotion.FEAR

    def test_dengue_triggers_fear(self, sim):
        ws = sim.simulate("brote de dengue en varios estados del sureste")
        cdmx = next(s for s in ws.states if s.state_code == "CDMX")
        assert cdmx.emotion == Emotion.FEAR

    # Technology — anger
    def test_whatsapp_outage_triggers_anger(self, sim):
        ws = sim.simulate("se cayo whatsapp en todo el pais")
        cdmx = next(s for s in ws.states if s.state_code == "CDMX")
        assert cdmx.emotion == Emotion.ANGER

    def test_hackeo_triggers_anger(self, sim):
        ws = sim.simulate("hackeo masivo a bancos mexicanos")
        cdmx = next(s for s in ws.states if s.state_code == "CDMX")
        assert cdmx.emotion == Emotion.ANGER

    # Pride / achievement — hope
    def test_orgullo_mexicano_triggers_hope(self, sim):
        ws = sim.simulate("mexicana destaca con innovacion en cancer")
        cdmx = next(s for s in ws.states if s.state_code == "CDMX")
        assert cdmx.emotion == Emotion.HOPE

    # Food — joy
    def test_tacos_triggers_joy(self, sim):
        ws = sim.simulate("tacos mexicanos son nombrados patrimonio gastronomico")
        cdmx = next(s for s in ws.states if s.state_code == "CDMX")
        assert cdmx.emotion == Emotion.JOY

    # Migration — sadness
    def test_deportacion_triggers_sadness(self, sim):
        ws = sim.simulate("deportacion masiva de mexicanos en la frontera")
        chis = next(s for s in ws.states if s.state_code == "CHIS")
        assert chis.emotion == Emotion.SADNESS


# ── Deduplication bug fix ──────────────────────────────────────────────────────

class TestMatchingAlgorithm:
    """Tests for the improved _match_rule scoring algorithm."""

    def test_no_duplicate_counting_for_accented_keywords(self, sim):
        """'huracan' and 'huracán' normalize to the same string — should count as 1 hit."""
        from pulso.engine.keyword_simulator import _match_rule
        _, hits = _match_rule("huracan devastador en quintana roo")
        # Without dedup fix this would be 2; after fix it should be 1
        assert hits == 1

    def test_multiword_keyword_beats_single_word_on_tie(self, sim):
        """'crisis economica' (14 chars) beats a single-word match in tie-break."""
        from pulso.engine.keyword_simulator import _match_rule
        rule, hits = _match_rule("crisis economica en el pais")
        assert rule["emotion"] == "sadness"

    def test_eleccion_substring_in_seleccion_does_not_win(self, sim):
        """'eleccion' must not beat 'seleccion' via substring false-match."""
        from pulso.engine.keyword_simulator import _match_rule
        rule, _ = _match_rule("la seleccion juega hoy")
        # Should be sports (joy), NOT elections (anger)
        assert rule["emotion"] == "joy"

    def test_higher_hit_count_wins(self, sim):
        """A rule with 2 keyword hits beats one with 1 hit."""
        ws = sim.simulate("gol de la seleccion en el mundial")
        cdmx = next(s for s in ws.states if s.state_code == "CDMX")
        assert cdmx.emotion == Emotion.JOY
