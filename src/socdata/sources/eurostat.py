from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

try:
    import eurostat  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    eurostat = None  # type: ignore

from .base import BaseAdapter
from ..core.types import DatasetSummary


class EurostatAdapter(BaseAdapter):
    def list_datasets(self) -> List[DatasetSummary]:
        """List available Eurostat datasets."""
        if eurostat is None:
            # Return minimal curated examples if eurostat package not available
            return [
                DatasetSummary(id="eurostat:une_rt_m", source="eurostat", title="Unemployment rate - monthly"),
                DatasetSummary(id="eurostat:demo_r_pjangroup", source="eurostat", title="Population on 1 January by age group, sex and NUTS 3 region"),
            ]
        
        try:
            # Try to get dataset list from Eurostat API
            datasets = []
            # Common Eurostat datasets - expanded list
            common_datasets = [
                ("une_rt_m", "Unemployment rate - monthly"),
                ("demo_r_pjangroup", "Population on 1 January by age group, sex and NUTS 3 region"),
                ("nama_10_gdp", "GDP and main components"),
                ("nama_10_p3", "Final consumption expenditure of households"),
                ("lfsq_egan2", "Employment by sex, age and educational attainment level"),
                ("ilc_li02", "At-risk-of-poverty rate by poverty threshold, age and sex"),
                ("edat_lfse_03", "Early leavers from education and training by sex and age"),
                ("hlth_silc_10", "Self-perceived health by sex, age and educational attainment level"),
                ("crim_hom_soff", "Intentional homicide offences"),
                ("migr_imm1ctz", "Immigration by age group, sex and citizenship"),
            ]
            
            for code, title in common_datasets:
                datasets.append(DatasetSummary(id=f"eurostat:{code}", source="eurostat", title=title))
            
            return datasets
        except Exception:
            # Fallback to minimal list if API fails
            return [
                DatasetSummary(id="eurostat:une_rt_m", source="eurostat", title="Unemployment rate - monthly"),
                DatasetSummary(id="eurostat:demo_r_pjangroup", source="eurostat", title="Population on 1 January by age group, sex and NUTS 3 region"),
            ]

    def load(self, dataset_id: str, *, filters: Dict[str, Any]) -> pd.DataFrame:
        if eurostat is None:
            raise RuntimeError("eurostat extra not installed. Install with: pip install socdata[eurostat]")
        _, code = dataset_id.split(":", 1)
        # eurostat.get_data_df handles filters via 'filter_pars'
        # eurostat.get_data_df requires dict for filter_pars; pass {} if none
        df = eurostat.get_data_df(code, filter_pars=filters or {})
        return df

    def ingest(self, *, file_path: str) -> pd.DataFrame:  # not applicable
        raise NotImplementedError("Eurostat adapter does not support ingest() from file")

