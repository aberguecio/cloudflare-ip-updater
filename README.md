# Clodflare-ip-updater
Updatea la ip de todos los dominios que quieras en cloudflare con tu ip local.
Para que se actualisen tienes que poner "update" en el comment.

Agregalo en un cronjob para que se ejecute de manera periodica.

## tokens
crea el archivo tokens.json
´´´
{
    "email": "tu_mail",
    "api_token": "tu_api_token",
    "zone_id": "tu_zone_id",
}
´´´