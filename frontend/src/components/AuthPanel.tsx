"use client";

import { useEffect, useState } from "react";
import type { User } from "@supabase/supabase-js";

import { createClient } from "@/lib/supabase/client";

export function AuthPanel() {
  const supabase = createClient();

  const [user, setUser] = useState<User | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authMessage, setAuthMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => {
      setUser(data.user);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });

    return () => subscription.unsubscribe();
  }, [supabase.auth]);

  async function signUp() {
    setIsLoading(true);
    setAuthMessage("");

    const { error } = await supabase.auth.signUp({
      email,
      password,
    });

    if (error) {
      setAuthMessage(error.message);
    } else {
      setAuthMessage("Account created. Check your email.");
    }

    setIsLoading(false);
  }

  async function signIn() {
    setIsLoading(true);
    setAuthMessage("");

    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (error) {
      setAuthMessage(error.message);
    } else {
      setAuthMessage("Signed in successfully.");
    }

    setIsLoading(false);
  }

  async function signOut() {
    await supabase.auth.signOut();
    setAuthMessage("Signed out.");
  }

  if (user) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <p className="text-sm text-slate-600">Signed in as</p>
        <p className="mt-1 text-sm font-semibold text-slate-950">
          {user.email}
        </p>
        <button
          type="button"
          onClick={signOut}
          className="mt-3 h-9 rounded-md bg-slate-950 px-4 text-sm font-semibold text-white"
        >
          Log out
        </button>
        {authMessage ? (
          <p className="mt-3 text-sm text-slate-600">{authMessage}</p>
        ) : null}
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="text-lg font-bold text-slate-950">Account</h2>

      <div className="mt-4 space-y-3">
        <input
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="Email"
          className="h-10 w-full rounded-md border border-slate-300 px-3 text-sm text-slate-900 outline-none placeholder:text-slate-600 focus:border-red-600"
        />

        <input
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          placeholder="Password"
          type="password"
          className="h-10 w-full rounded-md border border-slate-300 px-3 text-sm text-slate-900 outline-none placeholder:text-slate-600 focus:border-red-600"
        />

        <div className="grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={signIn}
            disabled={isLoading}
            className="h-10 rounded-md bg-red-600 text-sm font-semibold text-white hover:bg-red-700 disabled:bg-slate-400"
          >
            Log in
          </button>

          <button
            type="button"
            onClick={signUp}
            disabled={isLoading}
            className="h-10 rounded-md border border-red-600 text-sm font-semibold text-red-700 hover:bg-red-50 disabled:border-slate-300 disabled:text-slate-400"
          >
            Sign up
          </button>
        </div>

        {authMessage ? (
          <p className="text-sm font-medium text-slate-700">{authMessage}</p>
        ) : null}
      </div>
    </div>
  );
}
