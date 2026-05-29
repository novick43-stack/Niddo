/**
 * Auth0 Action — Post Login
 * ─────────────────────────
 * Agrega el rol del usuario al ID Token y al Access Token.
 *
 * Cómo configurarlo en Auth0:
 * 1. Ir a Actions → Library → Create Action → "Build from scratch"
 * 2. Nombre: "Add role to token"
 * 3. Trigger: "Login / Post Login"
 * 4. Pegar este código y hacer Deploy
 * 5. Ir a Actions → Flows → Login → arrastrar esta Action al flow
 *
 * El rol se lee de app_metadata del usuario. La primera vez que
 * alguien se loguea, Flask lo setea automáticamente vía Supabase.
 * Para setearlo manualmente en el dashboard de Auth0:
 *   User → app_metadata → { "role": "admin" }  o  { "role": "vecino" }
 */

exports.onExecutePostLogin = async (event, api) => {
  const namespace = 'https://niddo.app';
  const role = event.user.app_metadata?.role || 'vecino';

  // Agrega el rol al ID Token (usado por el frontend)
  api.idToken.setCustomClaim(`${namespace}/role`, role);

  // Agrega el rol al Access Token (usado por APIs)
  api.accessToken.setCustomClaim(`${namespace}/role`, role);
};
