# Desplegar tu propia copia

Esta guía lleva a quien bifurca el repositorio desde cero hasta un sitio
publicado en su cuenta de Cloudflare, con ejecución de código y cuentas. Qué
hace cada pieza está en [runner.md](runner.md). Aquí solo hay pasos.

Los valores entre `< >` son tuyos. `<worker>` es el nombre del Worker y `<host>`
es su dirección, por ejemplo `<worker>.<subdominio>.workers.dev`. Ningún secreto
va en el repositorio ni en un archivo que subas a git.

## Qué necesitas

- Una cuenta de Cloudflare con el plan Workers Paid, que los Containers
  requieren.
- [mise](https://mise.jdx.dev/), [bun](https://bun.sh/) y Docker en el `PATH`.
  `cf deploy` construye la imagen del corredor en tu equipo, con las versiones
  de Python y de uv que `mise.toml` fija y que
  `runner/worker/cloudflare.config.ts` lee con `mise current`.
- Una cuenta de Google y una de GitHub, para registrar los clientes OAuth.

```sh
cd runner/worker
bun install
bunx cf auth login
```

## 1. Elige el nombre del Worker

El nombre está en `worker.name` de
[`cloudflare.config.ts`](../runner/worker/cloudflare.config.ts). Si quieres otro
distinto de `qiskit-guides`, cámbialo ahí. El nombre fija `<host>`. Un dominio
propio va en el campo `domains` de `worker`; con uno, usa ese dominio como
`<host>` en todo lo que sigue.

## 2. Crea la base de datos

La base guarda cuentas, progreso e intentos. Su esquema es
[`src/schema.sql`](../runner/worker/src/schema.sql).

```sh
bunx cf d1 create --name qiskit-guides
```

Copia el identificador (`uuid`) de la respuesta. El nombre debe ser el de
`bindings.d1` en `cloudflare.config.ts`. Aplica el esquema:

```sh
bunx cf d1 query <uuid> "--sql=$(cat src/schema.sql)"
```

Escribe `--sql=` pegado al texto. El esquema empieza por `--`, y sin el `=` la
CLI lo toma por una bandera. No hay migraciones: para cambiar el esquema, borra
la base (`bunx cf d1 delete <uuid>`), crea otra y aplica el archivo de nuevo.

## 3. Crea el widget de Turnstile

```sh
bunx cf turnstile widgets create --name qiskit-guides --domains <host> --widget-mode managed
```

De la respuesta copia dos valores:

- La clave del sitio (`sitekey`) es pública. Escríbela en `TURNSTILE_SITE_KEY`
  de `cloudflare.config.ts`.
- El secreto (`secret`) se guarda en el paso 7 como `TURNSTILE_SECRET`.

## 4. Crea el cliente de Google

1. Abre [Google Auth Platform](https://console.cloud.google.com/auth/overview)
   en un proyecto de Google Cloud, nuevo o existente.
2. Si es la primera vez, pulsa **Get started**. Pon el nombre de la aplicación,
   tu correo de soporte y, en **Audience**, elige **External**. Pon un correo de
   contacto y acepta la política.
3. En **Data Access**, pulsa **Add or remove scopes** y marca `openid`,
   `.../auth/userinfo.email` y `.../auth/userinfo.profile`. Guarda.
4. En **Audience**, pulsa **Publish app**. Hasta entonces solo entran las
   cuentas de la lista de **Test users**.
5. En **Clients**, pulsa **Create client**. En **Application type** elige **Web
   application** y ponle un nombre.
6. En **Authorized redirect URIs** añade `https://<host>/auth/google/callback`.
   No pongas barra final.
7. Pulsa **Create**. Copia el **Client ID** y el **Client secret**: son
   `GOOGLE_CLIENT_ID` y `GOOGLE_CLIENT_SECRET`.

Qué pide el Worker a cada proveedor está en [Entrar](runner.md#entrar).

## 5. Crea la aplicación de GitHub

1. Abre
   [Developer settings > OAuth Apps](https://github.com/settings/developers) y
   pulsa **New OAuth App**.
2. Pon un nombre y, en **Homepage URL**, `https://<host>`.
3. En **Authorization callback URL** pon `https://<host>/auth/github/callback`.
   Deja **Enable Device Flow** sin marcar.
4. Pulsa **Register application**. Copia el **Client ID**: es
   `GITHUB_CLIENT_ID`.
5. Pulsa **Generate a new client secret** y cópialo: es `GITHUB_CLIENT_SECRET`.

## 6. Despliega

El primer despliegue sube también el secreto de Turnstile. `--secrets-file` lee
un `.env` que se borra enseguida.

```sh
bunx cf deploy --dry-run   # construye la imagen y el Worker, no sube nada
umask 077
read -rs -p 'Secreto de Turnstile: ' secret && printf 'TURNSTILE_SECRET=%s\n' "$secret" > "$TMPDIR/secrets.env"
bunx cf deploy --secrets-file "$TMPDIR/secrets.env"
rm "$TMPDIR/secrets.env"
```

Para publicar un cambio de las lecciones o del Worker, vuelve a ejecutar
`bunx cf deploy`.

## 7. Guarda los secretos de OAuth

El Worker ya existe, así que se le pueden añadir los cuatro secretos. Repite el
comando con cada nombre:

```sh
read -rs -p 'Valor: ' value && bunx cf workers secrets update <NAME> --worker <worker> --text "$value"
```

| `<NAME>`               | Valor                                       |
| ---------------------- | ------------------------------------------- |
| `GOOGLE_CLIENT_ID`     | El Client ID del paso 4.                    |
| `GOOGLE_CLIENT_SECRET` | El Client secret del paso 4.                |
| `GITHUB_CLIENT_ID`     | El Client ID del paso 5.                    |
| `GITHUB_CLIENT_SECRET` | El client secret del paso 5.                |
| `TURNSTILE_SECRET`     | Solo para cambiarlo: el secreto del paso 3. |

Sin `--text` la CLI no envía ningún valor. Cada comando crea una versión nueva
del Worker. Mientras falte el cliente de un proveedor, `/auth/<proveedor>`
responde 503 y el otro sigue funcionando.

## 8. Comprueba

```sh
curl -s https://<host>/health
curl -s https://<host>/api/me
curl -sI https://<host>/auth/google | grep -i '^location'
curl -sI https://<host>/auth/github | grep -i '^location'
```

`/health` responde 200 y `/api/me` responde `{"signedIn":false}`. Las dos
últimas imprimen una dirección de `accounts.google.com` y de `github.com` con
`redirect_uri=https://<host>/auth/<proveedor>/callback`. Esa dirección debe ser
la que registraste en los pasos 4 y 5, letra por letra. Después abre el sitio,
entra con cada proveedor y ejecuta un ejercicio.

El cron diario de [Retención](runner.md#retención) se declara en
`cloudflare.config.ts` y se despliega con el Worker.
