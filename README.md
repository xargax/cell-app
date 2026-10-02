# Настройка секретов в Streamlit Cloud

1. В Google Cloud Console создайте сервисный аккаунт и сгенерируйте JSON-ключ.
2. Предоставьте доступ сервисному аккаунту (его почте `...@...gserviceaccount.com`):
   - К файлу весов `best.pt` на Google Диске (роль: Читатель).
   - К Google Таблице с листами `users` и `sessions` (роль: Редактор).
3. В структуре Google Таблицы подготовьте заголовки:
   - Лист `users`: `email`, `password_hash`, `created_at`
   - Лист `sessions`: `email`, `timestamp`, `image_count`, `counts_per_image`, `concentration`
4. В панели Streamlit Cloud (App settings -> Secrets) вставьте:

```toml
[gcp_service_account]
type = "service_account"
project_id = "your-project"
private_key_id = "key-id"
private_key = "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----\n"
client_email = "sa-cell-counter@your-project.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "[https://accounts.google.com/o/oauth2/auth](https://accounts.google.com/o/oauth2/auth)"
token_uri = "[https://oauth2.googleapis.com/token](https://oauth2.googleapis.com/token)"
auth_provider_x509_cert_url = "[https://www.googleapis.com/oauth2/v1/certs](https://www.googleapis.com/oauth2/v1/certs)"
client_x509_cert_url = "..."
