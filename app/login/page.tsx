import { loginAction } from "@/lib/actions/auth";

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const { error } = await searchParams;

  return (
    <main>
      <h1>Connexion</h1>
      {error === "invalid_credentials" && <p role="alert">Email ou mot de passe incorrect.</p>}
      <form action={loginAction}>
        <div>
          <label>
            Email
            <br />
            <input type="email" name="email" required />
          </label>
        </div>
        <div>
          <label>
            Mot de passe
            <br />
            <input type="password" name="password" required />
          </label>
        </div>
        <button type="submit">Se connecter</button>
      </form>
      <p>
        Pas encore de compte ? <a href="/signup">Créer un workspace</a>
      </p>
    </main>
  );
}
