import { createBrowserClient } from "@supabase/ssr";
import type { SupabaseClient } from "@supabase/supabase-js";

let browserClient: SupabaseClient | undefined;

export function createClient() {
  if (!browserClient) {
    browserClient = createBrowserClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!
    );
  }

  return browserClient;
}

export async function getFreshAccessToken() {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session) {
    return null;
  }

  const expiresAt = session.expires_at ? session.expires_at * 1000 : 0;
  const shouldRefresh = expiresAt > 0 && expiresAt - Date.now() < 60_000;

  if (shouldRefresh) {
    const {
      data: { session: refreshedSession },
    } = await supabase.auth.refreshSession();

    return refreshedSession?.access_token ?? null;
  }

  const { error } = await supabase.auth.getUser(session.access_token);
  if (!error) {
    return session.access_token;
  }

  const {
    data: { session: refreshedSession },
  } = await supabase.auth.refreshSession();

  if (!refreshedSession) {
    await supabase.auth.signOut();
    return null;
  }

  const { error: refreshValidationError } = await supabase.auth.getUser(
    refreshedSession.access_token
  );

  if (refreshValidationError) {
    await supabase.auth.signOut();
    return null;
  }

  return refreshedSession.access_token;
}

export async function refreshAccessToken() {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.refreshSession();

  return session?.access_token ?? null;
}
