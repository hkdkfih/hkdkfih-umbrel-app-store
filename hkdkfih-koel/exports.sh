export APP_HKDKFIH_KOEL_DB_PASSWORD="$(derive_entropy "${app_entropy_identifier}-db-password")"
export APP_HKDKFIH_KOEL_APP_KEY="base64:$(printf '%s' "$(derive_entropy "${app_entropy_identifier}-app-key" | head -c32)" | base64)"
