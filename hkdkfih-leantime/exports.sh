export APP_HKDKFIH_LEANTIME_DB_PASSWORD="$(derive_entropy "${app_entropy_identifier}-db-password")"
export APP_HKDKFIH_LEANTIME_DB_ROOT_PASSWORD="$(derive_entropy "${app_entropy_identifier}-db-root-password")"
export APP_HKDKFIH_LEANTIME_SESSION_PASSWORD="$(derive_entropy "${app_entropy_identifier}-session-password")"
