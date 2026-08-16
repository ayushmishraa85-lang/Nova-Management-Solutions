"""
data_engine.universal_reader
────────────────────────────────
Reads any structured or semi-structured business file — CSV, TSV, Excel
(xls/xlsx/xlsm, multi-sheet), JSON, JSONL, XML, Parquet, ODS — into pandas
DataFrame(s), without assuming a fixed schema or a fixed file format.
Multi-sheet workbooks return every sheet so the caller can offer a picker
instead of silently guessing which one matters. Every failure path returns
a specific, human-readable reason instead of raising a raw traceback —
never just "upload failed."
"""

import json

import pandas as pd


class UniversalReader:
    def read(self, uploaded_file) -> dict:
        """Returns:
        {
          "ok": bool,
          "error": str | None,
          "sheets": {sheet_name: DataFrame, ...},   # >=1 entry when ok
          "default_sheet": str | None,
          "format": str,
        }
        """
        filename = uploaded_file.name
        ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
        try:
            if ext == "csv":
                return self._read_delimited(uploaded_file, sep=None, fmt="CSV")
            if ext == "tsv":
                return self._read_delimited(uploaded_file, sep="\t", fmt="TSV")
            if ext in ("xlsx", "xlsm"):
                return self._read_excel(uploaded_file, engine="openpyxl", fmt="Excel")
            if ext == "xls":
                return self._read_excel(uploaded_file, engine="xlrd", fmt="Excel (legacy .xls)")
            if ext == "ods":
                return self._read_excel(uploaded_file, engine="odf", fmt="OpenDocument Spreadsheet")
            if ext == "json":
                return self._read_json(uploaded_file)
            if ext == "jsonl":
                return self._read_jsonl(uploaded_file)
            if ext == "xml":
                return self._read_xml(uploaded_file)
            if ext == "parquet":
                return self._read_parquet(uploaded_file)
        except ImportError as e:
            return self._fail(f"Reading .{ext} files needs a package that isn't installed yet ({e}). "
                               f"Ask your developer to add it to requirements.txt.", ext)
        except Exception as e:
            return self._fail(f"Couldn't read this .{ext} file: {e}", ext)

        return self._fail(
            f"'.{ext}' isn't a structured/semi-structured format NovaMS can turn into a dataset yet "
            f"(supported: CSV, TSV, XLS/XLSX/XLSM, JSON, JSONL, XML, Parquet, ODS). "
            f"PDF/Word/PowerPoint/image support is planned but not live yet.",
            ext,
        )

    def _fail(self, msg: str, ext: str) -> dict:
        return dict(ok=False, error=msg, sheets={}, default_sheet=None, format=(ext or "unknown").upper())

    def _read_delimited(self, f, sep, fmt) -> dict:
        raw = f.read()
        f.seek(0)
        sample = raw[:4096].decode("utf-8", errors="replace") if isinstance(raw, bytes) else str(raw)[:4096]
        if sep is None:
            sep = "\t" if sample.count("\t") > sample.count(",") else ","
        df = pd.read_csv(f, sep=sep)
        if df.empty:
            return self._fail(f"{fmt} file was read but contains no data rows.", fmt.lower())
        return dict(ok=True, error=None, sheets={"Sheet1": df}, default_sheet="Sheet1", format=fmt)

    def _read_excel(self, f, engine, fmt) -> dict:
        xls = pd.ExcelFile(f, engine=engine)
        sheets = {}
        for name in xls.sheet_names:
            try:
                parsed = xls.parse(name)
                if not parsed.empty:
                    sheets[name] = parsed
            except Exception:
                continue  # skip an unreadable sheet rather than failing the whole workbook
        if not sheets:
            return self._fail(f"{fmt} file was read but every sheet is empty or unreadable.", "xlsx")
        default = max(sheets, key=lambda k: len(sheets[k]))  # default to the largest sheet
        return dict(ok=True, error=None, sheets=sheets, default_sheet=default, format=fmt)

    def _read_json(self, f) -> dict:
        raw = json.load(f)
        if isinstance(raw, list):
            df = pd.json_normalize(raw)
        elif isinstance(raw, dict):
            list_field = next((v for v in raw.values() if isinstance(v, list) and v and isinstance(v[0], dict)), None)
            df = pd.json_normalize(list_field) if list_field is not None else pd.json_normalize([raw])
        else:
            return self._fail("JSON file's top level isn't an object or array NovaMS can flatten into a table.", "json")
        if df.empty:
            return self._fail("JSON file was read but no tabular records were found.", "json")
        return dict(ok=True, error=None, sheets={"Sheet1": df}, default_sheet="Sheet1", format="JSON")

    def _read_jsonl(self, f) -> dict:
        text = f.read()
        text = text.decode("utf-8", errors="replace") if isinstance(text, bytes) else text
        records = [json.loads(line) for line in text.splitlines() if line.strip()]
        if not records:
            return self._fail("JSONL file was read but contains no records.", "jsonl")
        df = pd.json_normalize(records)
        return dict(ok=True, error=None, sheets={"Sheet1": df}, default_sheet="Sheet1", format="JSONL")

    def _read_xml(self, f) -> dict:
        try:
            df = pd.read_xml(f)
        except Exception as e:
            return self._fail(f"Couldn't find a repeating record structure in this XML file to turn into a table ({e}).", "xml")
        if df.empty:
            return self._fail("XML file was read but no records were found.", "xml")
        return dict(ok=True, error=None, sheets={"Sheet1": df}, default_sheet="Sheet1", format="XML")

    def _read_parquet(self, f) -> dict:
        df = pd.read_parquet(f)
        if df.empty:
            return self._fail("Parquet file was read but contains no data rows.", "parquet")
        return dict(ok=True, error=None, sheets={"Sheet1": df}, default_sheet="Sheet1", format="Parquet")
