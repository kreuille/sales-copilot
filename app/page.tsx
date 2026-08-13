import { redirect } from "next/navigation";
import { auth } from "@/auth";
import { getFirstWorkspaceForUser } from "@/lib/data/workspaces";

export default async function HomePage() {
  const session = await auth();
  if (!session?.user?.id) {
    redirect("/login");
  }
  const workspace = await getFirstWorkspaceForUser(session.user.id);
  redirect(workspace ? `/w/${workspace.id}` : "/signup");
}
