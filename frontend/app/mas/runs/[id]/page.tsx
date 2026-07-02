import { MasRunDetailPage } from '@/components/mas/mas-run-detail-page';


export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <MasRunDetailPage runId={id} />;
}
