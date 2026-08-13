import type { NextAuthConfig } from "next-auth";
import Credentials from "next-auth/providers/credentials";
import { getUserByEmail } from "@/lib/data/users";
import { verifyPassword } from "@/lib/auth/password";

// JWT session strategy on purpose: no Session/Account tables exist in
// prisma/schema.prisma (data-architecture.md doesn't call for them, and this
// product has a single credentials provider, not OAuth) — adding a DB
// adapter here would be an abstraction with no consumer (CLAUDE.md
// "no premature abstraction").
export const authConfig: NextAuthConfig = {
  session: { strategy: "jwt" },
  providers: [
    Credentials({
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      authorize: async (credentials) => {
        const email = credentials?.email;
        const password = credentials?.password;
        if (typeof email !== "string" || typeof password !== "string") {
          return null;
        }
        const user = await getUserByEmail(email);
        if (!user) {
          return null;
        }
        const valid = await verifyPassword(password, user.passwordHash);
        if (!valid) {
          return null;
        }
        return { id: user.id, email: user.email, name: user.name ?? undefined };
      },
    }),
  ],
  callbacks: {
    jwt({ token, user }) {
      if (user) {
        token.userId = user.id;
      }
      return token;
    },
    session({ session, token }) {
      if (typeof token.userId === "string") {
        session.user.id = token.userId;
      }
      return session;
    },
  },
};
