from vuelavuela.api import get_forecast_cached


def test_cache():
    hits = get_forecast_cached.cache_info().hits
    for i in range(4):
        get_forecast_cached(0, 0, i)
    assert hits == get_forecast_cached.cache_info().hits
    for i in range(4):
        get_forecast_cached(0, 0, 0)
    assert hits < get_forecast_cached.cache_info().hits
