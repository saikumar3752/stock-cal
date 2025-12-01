import { createClient } from '@supabase/supabase-js';
import { ArrowLeftIcon } from '@heroicons/react/24/solid';
import Link from 'next/link';

// FORCE DYNAMIC RENDERING
export const dynamic = 'force-dynamic';

// FIX: Update the type definition for params (Next.js 15 requirement)
export default async function NewsPage({ params }: { params: Promise<{ slug: string }> }) {
  // 1. Await the params (CRITICAL FIX)
  const resolvedParams = await params;
  const slug = decodeURIComponent(resolvedParams.slug);

  const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );

  // 2. Fetch the article
  const { data: article } = await supabase
    .from('news_articles')
    .select('*')
    .eq('slug', slug)
    .single();

  if (!article) {
    return (
      <div className="min-h-screen bg-slate-950 text-white flex flex-col items-center justify-center p-4">
        <h1 className="text-2xl font-bold mb-2">Analysis Not Found</h1>
        <p className="text-slate-400 mb-6">We couldn't find the report for "{slug}".</p>
        <Link href="/" className="text-blue-400 hover:underline">Return to Dashboard</Link>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-white text-slate-900 font-sans">
      {/* Top Bar */}
      <div className="bg-slate-950 py-4 px-6 sticky top-0 z-50 border-b border-slate-800">
        <div className="max-w-3xl mx-auto flex items-center">
            <Link href="/" className="text-slate-400 hover:text-white flex items-center gap-2 text-sm font-medium transition-colors">
                <ArrowLeftIcon className="h-4 w-4" /> Back to Dashboard
            </Link>
        </div>
      </div>

      <article className="max-w-3xl mx-auto p-6 md:p-12">
        {/* Meta */}
        <div className="mb-6">
             <span className="bg-blue-100 text-blue-800 text-xs font-bold px-2 py-1 rounded uppercase tracking-wide">
                {article.symbol.replace('.NS','')}
             </span>
             <span className="text-slate-500 text-sm ml-3">
                {new Date(article.published_at).toLocaleDateString('en-IN', { year: 'numeric', month: 'long', day: 'numeric' })}
             </span>
        </div>

        {/* Headline */}
        <h1 className="text-3xl md:text-5xl font-bold text-slate-900 mb-8 leading-tight">
            {article.title}
        </h1>
        
        {/* CONTENT BODY (Renders HTML from DB) */}
        <div 
          className="prose prose-lg max-w-none prose-headings:font-bold prose-h2:text-2xl prose-h2:mt-8 prose-h2:mb-4 prose-p:text-slate-700 prose-p:leading-relaxed prose-a:text-blue-600 prose-strong:text-slate-900 prose-li:text-slate-700"
          dangerouslySetInnerHTML={{ __html: article.content }} 
        />

        {/* CALL TO ACTION */}
        <div className="mt-12 p-8 bg-slate-50 border border-slate-200 rounded-2xl text-center">
          <h3 className="font-bold text-2xl text-slate-900 mb-2">Trade this Insight</h3>
          <p className="text-slate-600 mb-6">Don't just read the news. Execute this trade instantly on our partner platform.</p>
          <a href="https://upstox.com/open-account/?f=Z773" target="_blank" className="inline-flex items-center justify-center bg-blue-600 text-white px-8 py-4 rounded-xl font-bold text-lg hover:bg-blue-700 transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-1">
            Open Upstox Account &rarr;
          </a>
          <p className="text-xs text-slate-400 mt-4">Capital at risk. Fees may apply.</p>
        </div>
      </article>
    </main>
  );
}