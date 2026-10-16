// Estas rutas pasan por el Worker antes que los archivos de site/.
// Las demás las responde el servicio de archivos estáticos.
export const WORKER_FIRST = ["/run", "/health", "/auth/*", "/api/*"];
