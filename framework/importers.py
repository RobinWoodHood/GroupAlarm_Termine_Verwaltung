from typing import Iterator, Optional
import pandas as pd


class ExcelImporter:
    """Importer for Excel files using :mod:`pandas`.

    The importer caches the read DataFrame so modifications can be persisted back
    to disk with :meth:`save`.
    """

    def __init__(self, filename: str, sheet_name: Optional[str] = None, date_column: Optional[str] = None):
        """Create an ExcelImporter.

        Parameters
        ----------
        filename : str
            Path to the Excel file.
        sheet_name : str, optional
            Sheet name to read (default: first sheet).
        date_column : str, optional
            Optional column name used to filter out rows with missing dates.
        """
        self.filename = filename
        self.sheet_name = sheet_name
        self.date_column = date_column
        self._df = None

    def _load(self):
        """Internal helper for `load`."""
        if self._df is None:
            # pandas returns a dict of DataFrames for sheet_name=None.
            # For this importer, None means "first sheet".
            sheet = 0 if self.sheet_name is None else self.sheet_name
            self._df = pd.read_excel(self.filename, sheet_name=sheet, header=0)
        return self._df

    def rows(self) -> Iterator[pd.Series]:
        """Yield rows as :class:`pandas.Series` objects.

        Yields
        ------
        pandas.Series
            Rows from the loaded sheet, optionally filtered by ``date_column``.
        """
        df = self._load()
        if self.date_column:
            df = df[~df[self.date_column].isna()]
        for _, row in df.iterrows():
            yield row

    def set_value(self, index, column: str, value):
        """Set a value in the internal DataFrame at ``index`` and ``column``.

        The change is kept in memory until :meth:`save` is called.
        """
        df = self._load()
        df.at[index, column] = value

    def save(self):
        """Persist the current DataFrame back to the Excel file (overwrites file)."""
        # Write back to the same sheet/file; pandas will rewrite the file
        self._load().to_excel(self.filename, index=False)


class CSVImporter:
    """Importer for CSV files that supports read, in-memory mutation and save.

    The importer attempts multiple common encodings when reading (useful for
    Excel-generated CSV files). It preserves the detected encoding when saving.
    """

    def __init__(self, filename: str, delimiter: str = ',', date_column: Optional[str] = None, encoding: Optional[str] = 'cp1252'):
        """Create a CSVImporter.

        Parameters
        ----------
        filename : str
            Path to the CSV file.
        delimiter : str, optional
            Field delimiter (default: ',').
        date_column : str, optional
            Optional column name used to filter out rows with missing dates.
        encoding : str, optional
            Preferred encoding to try first when reading (default: 'cp1252').
        """
        self.filename = filename
        self.delimiter = delimiter
        self.date_column = date_column
        self.encoding = encoding
        self._df = None
        self._detected_encoding = None

    def _load(self):
        """Internal helper for `load`."""
        if self._df is None:
            encodings_to_try = [self.encoding, 'utf-8', 'utf-8-sig', 'utf-16', 'latin-1', 'cp1252']
            last_exc = None
            for enc in filter(None, dict.fromkeys(encodings_to_try)):
                try:
                    df = pd.read_csv(self.filename, sep=self.delimiter, header=0, encoding=enc)
                    self._df = df
                    self._detected_encoding = enc
                    break
                except Exception as exc:
                    last_exc = exc
                    continue
            else:
                raise last_exc
        return self._df

    def rows(self):
        """Yield rows as :class:`pandas.Series` objects.

        Yields
        ------
        pandas.Series
            Rows from the loaded CSV, optionally filtered by ``date_column``.
        """
        df = self._load()
        if self.date_column:
            df = df[~df[self.date_column].isna()]
        for _, row in df.iterrows():
            yield row

    def set_value(self, index, column: str, value):
        """Set a value in the internal DataFrame at ``index`` and ``column``.

        If ``column`` does not exist it will be created.
        """
        df = self._load()
        # Create column if necessary
        if column not in df.columns:
            df[column] = None
        df.at[index, column] = value

    def save(self):
        """Persist the DataFrame back to the CSV file using the detected encoding."""
        df = self._load()
        df.to_csv(self.filename, sep=self.delimiter, index=False, encoding=self._detected_encoding or self.encoding)
