export APP_HKDKFIH_MINIFLUX_DB_PASSWORD="$(derive_entropy "${app_entropy_identifier}-db-password")"
export APP_HKDKFIH_MINIFLUX_MEDIA_PROXY_KEY="$(derive_entropy "${app_entropy_identifier}-media-proxy-key")"
