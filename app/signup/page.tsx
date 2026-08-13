import { signupAction } from "@/lib/actions/auth";

const ERROR_MESSAGES: Record<string, string> = {
  missing_fields: "Email, mot de passe et nom du workspace sont requis.",
  email_taken: "Un compte existe déjà avec cet email.",
};

export default async function SignupPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const { error } = await searchParams;

  return (
    <main>
      <h1>Créer votre workspace</h1>
      {error && ERROR_MESSAGES[error] && <p role="alert">{ERROR_MESSAGES[error]}</p>}
      <form action={signupAction}>
        <div>
          <label>
            Nom
            <br />
            <input type="text" name="name" />
          </label>
        </div>
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
            <input type="password" name="password" required minLength={8} />
          </label>
        </div>
        <div>
          <label>
            Nom du workspace
            <br />
            <input type="text" name="workspaceName" required />
          </label>
        </div>
        <button type="submit">Créer</button>
      </form>
      <p>
        Déjà un compte ? <a href="/login">Se connecter</a>
      </p>
    </main>
  );
}
