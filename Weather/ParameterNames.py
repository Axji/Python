"""Sprechende Namen für die Parameterkürzel der MeteoSchweiz-Monatsdaten.

Die Bedeutung stammt aus ogd-nbcn_meta_parameters.csv (Spalte parameter_description_en); die Einheiten stehen in der
Tabelle `parameters` der Datenbank. "norm9120" ist die Referenzperiode 1991-2020. "dev" ist die Abweichung vom Normwert,
"ratio" das Verhältnis zum Normwert in Prozent.
"""

PARAMETER_NAMES = {
    # Lufttemperatur 2 m über Boden
    'ths200m0': 'temp_2m_mean',
    'ths2dymn': 'temp_2m_daily_min_mean',
    'ths2dymx': 'temp_2m_daily_max_mean',
    'thl200mn': 'temp_2m_abs_min',
    'thl200mx': 'temp_2m_abs_max',
    'th9120mv': 'temp_2m_mean_dev_norm9120',
    'th91dnmv': 'temp_2m_daily_min_mean_dev_norm9120',
    'th91dxmv': 'temp_2m_daily_max_mean_dev_norm9120',
    # Anzahl Tage bzw. Nächte pro Monat mit Temperaturschwelle
    'ths00nm0': 'frost_days',
    'ths00xm0': 'ice_days',
    'ths25xm0': 'summer_days',
    'ths30xm0': 'heat_days',
    'ths35xm0': 'very_hot_days',
    'ths20nm0': 'tropical_nights',
    # Gradtage
    'xhs000m0': 'heating_degree_days_hgt12_20',
    'xhs012m0': 'heating_degree_days_atd12_12',
    'xhs00om0': 'cooling_degree_days',
    # Niederschlag
    'rhs150m0': 'precip_total',
    'rhs001m0': 'precip_days_ge_1mm',
    'rh9120mv': 'precip_total_ratio_norm9120',
    # Luftdruck und Dampfdruck
    'phsstam0': 'pressure_qfe_mean',
    'ph9120mv': 'pressure_qfe_mean_dev_norm9120',
    'pva2hsm0': 'vapour_pressure_mean',
    'pv9120mv': 'vapour_pressure_mean_dev_norm9120',
    # Wind, Strahlung, Sonne
    'fhs010m0': 'wind_speed_mean',
    'fh9120mv': 'wind_speed_mean_ratio_norm9120',
    'ghs000m0': 'global_radiation_mean',
    'gh9120mv': 'global_radiation_mean_ratio_norm9120',
    'shs000m0': 'sunshine_duration_total',
    'sh9120mv': 'sunshine_duration_total_ratio_norm9120',
}


def parameter_name(code):
    """Gibt den sprechenden Namen zurück; unbekannte Kürzel bleiben unverändert."""
    return PARAMETER_NAMES.get(code, code)
