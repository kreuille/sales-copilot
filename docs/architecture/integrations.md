# Intégrations

## État V1 (A-004)
Aucune intégration externe réelle. Le produit fonctionne en **entrée/sortie manuelle** :
- Entrée : l'utilisateur colle du texte brut (notes de call, profils, pipeline) ou importe un CSV.
- Sortie : l'utilisateur copie le résultat ou exporte un CSV.

## Interfaces prévues (non implémentées), pour ne pas bloquer une évolution future (ADR-004)
```ts
interface CRMExportPort {
  exportDeals(workspaceId: string): Promise<CSVExport>
}

// Non implémenté en V1 — signature indicative pour la conception future
interface CRMSyncPort {
  pushDeal(workspaceId: string, deal: Deal): Promise<SyncResult>
  pullContacts(workspaceId: string): Promise<Contact[]>
}

// Non implémenté en V1
interface EmailSendPort {
  // Volontairement non détaillé : implique une politique d'approbation humaine
  // stricte (cf. brief "premier email à un prospect" = APPROVAL_REQUIRED)
  // à concevoir explicitement le jour où ce besoin est validé, pas avant.
}
```

## Candidats d'intégration mentionnés implicitement par le PDF (à valider avec l'utilisateur avant implémentation)
- CRM léger : Notion, Airtable (cités explicitement dans le prompt de l'Agent 17 "Mon CRM : NOTION / AIRTABLE / HUBSPOT / AUTRE").
- Email : non spécifié.
- LinkedIn : mentionné comme canal (DM), pas comme intégration API (LinkedIn restreint fortement l'automatisation — impliquerait une revue de conformité avant tout développement).

## Règle de gouvernance pour toute future intégration
Avant d'implémenter un connecteur réel : (1) confirmer le besoin avec l'utilisateur, (2) classer chaque action possible du connecteur en READ / WRITE / EXTERNAL_ACTION / COMMUNICATION_ACTION (taxonomie du brief), (3) toute EXTERNAL_ACTION ou COMMUNICATION_ACTION passe par le mode `APPROVAL_REQUIRED` défini dans [[governance]], jamais `AUTONOMOUS`.
