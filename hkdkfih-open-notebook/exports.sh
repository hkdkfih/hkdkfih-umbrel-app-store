export APP_HKDKFIH_OPEN_NOTEBOOK_ENCRYPTION_KEY="$(derive_entropy "${app_entropy_identifier}-encryption-key")"
export APP_HKDKFIH_OPEN_NOTEBOOK_DB_PASSWORD="$(derive_entropy "${app_entropy_identifier}-db-password")"
