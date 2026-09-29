# -*- coding: utf-8 -*-
"""Metadata, documentation parity, and discoverability contract tests."""

import unittest
from pathlib import Path

import usmc

ROOT = Path(__file__).resolve().parents[1]


class TestMetadataContract(unittest.TestCase):
    def test_readmes_exist(self):
        for name in ["README.md", "README_de.md", "README_es.md"]:
            path = ROOT / name
            self.assertTrue(path.exists(), f"{name} must exist")
            self.assertGreater(path.stat().st_size, 1000, f"{name} must not be empty")

    def test_language_switchers_linked(self):
        en_text = (ROOT / "README.md").read_text(encoding="utf-8")
        de_text = (ROOT / "README_de.md").read_text(encoding="utf-8")
        es_text = (ROOT / "README_es.md").read_text(encoding="utf-8")

        for text, filename in [(en_text, "README.md"), (de_text, "README_de.md"), (es_text, "README_es.md")]:
            with self.subTest(filename=filename):
                self.assertIn("[English](README.md)", text)
                self.assertIn("[Deutsch](README_de.md)", text)
                self.assertIn("[Español](README_es.md)", text)

    def test_test_badges_synchronized(self):
        en_text = (ROOT / "README.md").read_text(encoding="utf-8")
        de_text = (ROOT / "README_de.md").read_text(encoding="utf-8")
        es_text = (ROOT / "README_es.md").read_text(encoding="utf-8")

        self.assertIn("Tests-186%20passed", en_text)
        self.assertIn("Tests-186%20bestanden", de_text)
        self.assertIn("Tests-186%20aprobados", es_text)
        self.assertIn("Verified-2026--09--28", en_text)
        self.assertIn("Gepr%C3%BCft-2026--09--28", de_text)
        self.assertIn("Verificado-2026--09--28", es_text)
        for text in [en_text, de_text, es_text]:
            self.assertIn("Attribution-NOTICE-blue.svg", text)
            self.assertIn("Level%201%20SBOM-Text%20Companion-brightgreen.svg", text)

    def test_mermaid_sequence_diagram_present(self):
        for name in ["README.md", "README_de.md", "README_es.md"]:
            text = (ROOT / name).read_text(encoding="utf-8")
            with self.subTest(name=name):
                self.assertIn("```mermaid", text)
                self.assertIn("sequenceDiagram", text)
                self.assertIn("autonumber", text)
                self.assertIn("start_session", text)

    def test_llms_txt_updated(self):
        path = ROOT / "llms.txt"
        self.assertTrue(path.exists())
        text = path.read_text(encoding="utf-8")
        self.assertIn("Last-checked: 2026-09-28", text)
        self.assertIn("0.3.0", text)
        self.assertIn("README_es.md", text)
        self.assertIn("NOTICE", text)
        self.assertIn("THIRD_PARTY_LICENSES.md", text)
        self.assertIn("THIRD_PARTY_LICENSES.txt", text)
        self.assertIn("SECURITY.md", text)
        self.assertIn("MARKETING-LOG.txt", text)
        self.assertIn("186", text)
        self.assertIn("521 BGB", text)

    def test_hygiene_and_governance_files_exist(self):
        for name in [
            "NOTICE",
            "THIRD_PARTY_LICENSES.md",
            "THIRD_PARTY_LICENSES.txt",
            "MARKETING-LOG.txt",
            "SECURITY.md",
            "CHANGELOG.md",
            "LICENSE",
            ".gitignore",
        ]:
            path = ROOT / name
            with self.subTest(name=name):
                self.assertTrue(path.exists(), f"{name} must exist")
                self.assertGreater(path.stat().st_size, 50, f"{name} must not be empty")

    def test_ci_workflow_hardening(self):
        workflows = ROOT / ".github" / "workflows"
        self.assertTrue(workflows.exists())

        stale = (workflows / "stale.yml").read_text(encoding="utf-8")
        self.assertIn("actions/stale@v9", stale)
        self.assertIn("timeout-minutes: 10", stale)
        self.assertIn("concurrency:", stale)
        self.assertIn("cancel-in-progress: true", stale)

        welcome = (workflows / "welcome.yml").read_text(encoding="utf-8")
        self.assertIn("actions/first-interaction@v3", welcome)
        self.assertIn("timeout-minutes: 5", welcome)
        self.assertIn("concurrency:", welcome)
        self.assertIn("cancel-in-progress: true", welcome)

        auto_assign = (workflows / "auto-assign.yml").read_text(encoding="utf-8")
        self.assertIn("concurrency:", auto_assign)
        self.assertIn("cancel-in-progress: true", auto_assign)
        self.assertIn("timeout-minutes: 5", auto_assign)
        self.assertIn("issues: write", auto_assign)
        self.assertIn("pull-requests: write", auto_assign)

        label_sync = (workflows / "label-sync.yml").read_text(encoding="utf-8")
        self.assertIn("concurrency:", label_sync)
        self.assertIn("cancel-in-progress: true", label_sync)
        self.assertIn("timeout-minutes: 5", label_sync)

        ci = (workflows / "ci.yml").read_text(encoding="utf-8")
        self.assertIn("timeout-minutes: 15", ci)
        self.assertIn("concurrency:", ci)
        self.assertIn("cancel-in-progress: true", ci)
        self.assertIn("ruff check .", ci)

    def test_security_policy_bilingual_and_sla(self):
        sec = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
        self.assertIn("## Deutsch", sec)
        self.assertIn("## English", sec)
        self.assertIn("48 Stunden", sec)
        self.assertIn("48 hours", sec)
        self.assertIn("5 Werktagen", sec)
        self.assertIn("5 business days", sec)
        self.assertIn("https://github.com/ellmos-ai/usmc/security/advisories/new", sec)
        self.assertIn("security@ellmos.ai", sec)

    def test_third_party_licenses_invariants(self):
        tpl = (ROOT / "THIRD_PARTY_LICENSES.md").read_text(encoding="utf-8")
        self.assertIn("Zero-Copyleft Guarantee", tpl)
        self.assertIn("RunAsInvoker", tpl)
        self.assertIn("dependencies = []", tpl)
        for i in range(1, 11):
            inv = f"INV-{'LOCAL' if i == 1 else 'UNPRIV' if i == 2 else 'SQLITE' if i == 3 else 'SCHEMA' if i == 4 else 'BOUND' if i == 5 else 'FILTER' if i == 6 else 'LANG' if i == 7 else 'ISOL' if i == 8 else 'AUDIT' if i == 9 else 'SLA'}-{i:02d}"
            self.assertIn(inv, tpl)

    def test_version_consistency(self):
        self.assertEqual(usmc.__version__, "0.3.0")
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("## 0.3.0 - 2026-09-26", changelog)
        self.assertIn("## 0.2.3 - 2026-09-19", changelog)
        llms = (ROOT / "llms.txt").read_text(encoding="utf-8")
        self.assertIn("Source version is `0.3.0`", llms)

    def test_pyproject_toml_guardrails(self):
        pyproj = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('license-files = ["LICENSE", "NOTICE", "THIRD_PARTY_LICENSES.md", "THIRD_PARTY_LICENSES.txt"]', pyproj)
        self.assertIn('Notice = "https://github.com/ellmos-ai/usmc/blob/main/NOTICE"', pyproj)
        self.assertIn('minversion = "7.0"', pyproj)
        self.assertIn(".pytest_temp", pyproj)
        self.assertIn("--basetemp=.pytest_temp", pyproj)
        self.assertIn("[tool.ruff]", pyproj)

    def test_notice_attribution(self):
        notice = (ROOT / "NOTICE").read_text(encoding="utf-8")
        self.assertIn("usmc (United Shared Memory Client)", notice)
        self.assertIn("Copyright (c) 2026 Lukas Geiger", notice)
        self.assertIn("ellmos-ai", notice)
        self.assertIn("open-bricks", notice)
        self.assertIn("MIT License", notice)

    def test_level1_sbom_inventory(self):
        sbom = (ROOT / "THIRD_PARTY_LICENSES.txt").read_text(encoding="utf-8")
        self.assertIn("Audited: 2026-09-28", sbom)
        self.assertIn("RunAsInvoker", sbom)
        self.assertIn("dependencies = []", sbom)
        self.assertIn("Python Standard Library", sbom)
        self.assertIn("NOTICE", sbom)

    def test_eighteen_point_navigation_parity(self):
        en_text = (ROOT / "README.md").read_text(encoding="utf-8")
        de_text = (ROOT / "README_de.md").read_text(encoding="utf-8")
        es_text = (ROOT / "README_es.md").read_text(encoding="utf-8")

        en_anchors = [
            "#key-features",
            "#core-capabilities--primitives",
            "#target-personas--discoverability",
            "#comparative-matrix-vs-alternatives",
            "#architecture--data-flow",
            "#ascii-topology",
            "#multi-agent-interaction-sequence",
            "#governance--runtime-invariants",
            "#quick-start",
            "#core-concepts--primitives",
            "#finding-things--advanced-filtering",
            "#multi-agent-session-coordination",
            "#runtime-language-contract",
            "#database-schema--state-isolation",
            "#sibling-ecosystem--positioning",
            "#testing--quality-gates",
            "#third-party-licenses--transparency",
            "#security-policy--liability",
        ]
        de_anchors = [
            "#hauptmerkmale",
            "#kernkonzepte--primitive",
            "#zielgruppen--auffindbarkeit",
            "#vergleichsmatrix-gegenueber-alternativen",
            "#architektur--datenfluss",
            "#ascii-topologie",
            "#multi-agenten-interaktionssequenz",
            "#governance--laufzeit-invarianten",
            "#schnellstart",
            "#kernkonzepte--primitive",
            "#gezieltes-suchen--filterung",
            "#multi-agenten-sitzungskoordination",
            "#laufzeit-sprachvertrag",
            "#datenbankschema--status-isolation",
            "#geschwister-oekosystem--positionierung",
            "#testen--qualitaetstore",
            "#drittanbieter-lizenzen--transparenz",
            "#sicherheitsrichtlinie--haftung",
        ]
        es_anchors = [
            "#características-principales",
            "#capacidades-clave--primitivas",
            "#arquetipos-de-usuario--visibilidad",
            "#matriz-comparativa-frente-a-alternativas",
            "#arquitectura-y-flujo-de-datos",
            "#topologia-ascii",
            "#secuencia-de-interacción-multi-agente",
            "#invariantes-de-gobernanza-y-ejecución",
            "#inicio-rápido",
            "#conceptos-clave-y-primitivas",
            "#búsqueda-precisa-y-filtros",
            "#coordinación-de-sesiones-multi-agente",
            "#contrato-de-idioma-en-ejecución",
            "#esquema-de-base-de-datos-y-aislamiento",
            "#ecosistema-hermano-y-posicionamiento",
            "#pruebas-y-verificacion",
            "#licencias-de-terceros-y-transparencia",
            "#politica-de-seguridad-y-responsabilidad",
        ]

        self.assertEqual(len(en_anchors), 18)
        self.assertEqual(len(de_anchors), 18)
        self.assertEqual(len(es_anchors), 18)

        for anchor in en_anchors:
            self.assertIn(anchor, en_text, f"Missing English anchor: {anchor}")
        for anchor in de_anchors:
            self.assertIn(anchor, de_text, f"Missing German anchor: {anchor}")
        for anchor in es_anchors:
            self.assertIn(anchor, es_text, f"Missing Spanish anchor: {anchor}")

    def test_sec_dual_html_anchors_parity(self):
        en_text = (ROOT / "README.md").read_text(encoding="utf-8")
        de_text = (ROOT / "README_de.md").read_text(encoding="utf-8")
        es_text = (ROOT / "README_es.md").read_text(encoding="utf-8")

        for i in range(1, 19):
            tag = f'id="sec-{i:02d}"'
            link = f'#sec-{i:02d}'
            for text, name in [(en_text, "README.md"), (de_text, "README_de.md"), (es_text, "README_es.md")]:
                with self.subTest(sec=i, name=name):
                    self.assertIn(tag, text, f"Missing anchor {tag} in {name}")
                    self.assertIn(link, text, f"Missing link {link} in {name}")

    def test_ascii_topology_projection_present(self):
        en_text = (ROOT / "README.md").read_text(encoding="utf-8")
        de_text = (ROOT / "README_de.md").read_text(encoding="utf-8")
        es_text = (ROOT / "README_es.md").read_text(encoding="utf-8")

        self.assertIn("[VIEW 1: CLIENT RUNTIMES & AGENT DRIVERS]", en_text)
        self.assertIn("[VIEW 2: USMC CORE ENGINE & MEMORY PRIMITIVES]", en_text)
        self.assertIn("[VIEW 3: ACID WAL PERSISTENCE & CONCURRENCY]", en_text)

        self.assertIn("[SICHT 1: CLIENT-LAUFZEITEN & AGENTEN-TREIBER]", de_text)
        self.assertIn("[SICHT 2: USMC KERN-ENGINE & SPEICHER-PRIMITIVE]", de_text)
        self.assertIn("[SICHT 3: ACID WAL PERSISTENZ & KONKURRENZ]", de_text)

        self.assertIn("[VISTA 1: ENTORNOS CLIENTE Y CONTROLADORES DE AGENTES]", es_text)
        self.assertIn("[VISTA 2: MOTOR CENTRAL USMC Y PRIMITIVAS DE MEMORIA]", es_text)
        self.assertIn("[VISTA 3: PERSISTENCIA ACID WAL Y CONCURRENCIA]", es_text)

    def test_pep621_metadata_saturation(self):
        pyproj = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn("keywords = [", pyproj)
        self.assertIn('"agent-framework"', pyproj)
        self.assertIn('"zero-dependency"', pyproj)
        self.assertIn('"Plain-Text Licenses"', pyproj)
        self.assertIn('"Third-Party Licenses (Text)"', pyproj)
        self.assertIn('"Level 1 SBOM"', pyproj)

    def test_persona_tags_present(self):
        for name in ["README.md", "README_de.md", "README_es.md"]:
            text = (ROOT / name).read_text(encoding="utf-8")
            with self.subTest(name=name):
                for p in ["PERSONA-01", "PERSONA-02", "PERSONA-03", "PERSONA-04"]:
                    self.assertIn(p, text)

    def test_target_personas_present(self):
        mkt = (ROOT / "MARKETING-LOG.txt").read_text(encoding="utf-8")
        en = (ROOT / "README.md").read_text(encoding="utf-8")
        de = (ROOT / "README_de.md").read_text(encoding="utf-8")
        es = (ROOT / "README_es.md").read_text(encoding="utf-8")

        self.assertIn("Autonomous Multi-Agent Swarm Engineers", mkt)
        self.assertIn("Local-First & Zero-Egress Engineers", mkt)
        self.assertIn("Desktop App & MCP Tool Integrators", mkt)
        self.assertIn("Enterprise Security & Compliance Auditors", mkt)

        self.assertIn("Autonomous Multi-Agent Swarm Engineers", en)
        self.assertIn("Autonome Multi-Agenten-Entwickler", de)
        self.assertIn("Desarrolladores de enjambres multi-agente", es)

    def test_comparative_matrix_present(self):
        for name, key in [
            ("README.md", "Runtime Dependencies"),
            ("README_de.md", "Laufzeitabhängigkeiten"),
            ("README_es.md", "Dependencias en ejecución"),
            ("MARKETING-LOG.txt", "Runtime Dependencies"),
        ]:
            text = (ROOT / name).read_text(encoding="utf-8")
            with self.subTest(name=name):
                self.assertIn(key, text)
                self.assertIn("Mem0", text)
                self.assertIn("Redis", text)

    def test_governance_invariants_table(self):
        for name in ["README.md", "README_de.md", "README_es.md", "MARKETING-LOG.txt"]:
            text = (ROOT / name).read_text(encoding="utf-8")
            with self.subTest(name=name):
                for i in range(1, 11):
                    inv = f"INV-{'LOCAL' if i == 1 else 'UNPRIV' if i == 2 else 'SQLITE' if i == 3 else 'SCHEMA' if i == 4 else 'BOUND' if i == 5 else 'FILTER' if i == 6 else 'LANG' if i == 7 else 'ISOL' if i == 8 else 'AUDIT' if i == 9 else 'SLA'}-{i:02d}"
                    self.assertIn(inv, text)

    def test_sibling_ecosystem_linked(self):
        for name in ["README.md", "README_de.md", "README_es.md"]:
            text = (ROOT / name).read_text(encoding="utf-8")
            with self.subTest(name=name):
                self.assertIn("https://github.com/ellmos-ai/rinnsal", text)
                self.assertIn("https://github.com/ellmos-ai/bach", text)
                self.assertIn("https://github.com/ellmos-ai/skills", text)
                self.assertIn("https://github.com/ellmos-ai/connectors", text)
                self.assertIn("https://github.com/ellmos-ai/clutch", text)
                self.assertIn("https://github.com/ellmos-ai/policy-registry", text)
                self.assertIn("https://github.com/dev-bricks/DevCenter", text)
                self.assertIn("https://github.com/open-bricks", text)


if __name__ == "__main__":
    unittest.main()
