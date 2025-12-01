"use client";
import { createClient } from '@supabase/supabase-js';
import { Card, Title, Text, Badge, Table, TableHead, TableRow, TableHeaderCell, TableBody, TableCell, TextInput, Select, SelectItem } from "@tremor/react";
import { useEffect, useState } from 'react';
import { NewspaperIcon, ArrowTrendingUpIcon, BoltIcon, CalculatorIcon, MagnifyingGlassIcon } from '@heroicons/react/24/solid';
import Link from 'next/link';

// --- CONFIGURATION ---
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

export default function Home() {
  // --- STATE ---
  const [scans, setScans] = useState<any[]>([]);
  const [trades, setTrades] = useState<any[]>([]);
  const [articles, setArticles] = useState<any[]>([]);
  const [targets, setTargets] = useState<any[]>([]);
  const [indices, setIndices] = useState<any[]>([]);

  // Filter & Pagination State
  const [search, setSearch] = useState("");
  const [trendFilter, setTrendFilter] = useState("ALL");
  const [page, setPage] = useState(1);
  const rowsPerPage = 10;

  useEffect(() => {
    async function fetchData() {
      // 1. Market Indices
      const { data: idx } = await supabase.from('market_indices').select('*');
      if (idx) setIndices(idx);

      // 2. Bot Trades
      const { data: logs } = await supabase.from('trade_logs').select('*').order('created_at', { ascending: false });
      if (logs) setTrades(logs);

      // 3. News
      const { data: news } = await supabase.from('news_articles').select('*').order('published_at', { ascending: false }).limit(6);
      if (news) setArticles(news);

      // 4. Broker Targets
      const { data: brokerData } = await supabase.from('broker_targets').select('*').gt('upside_pct', 5).order('upside_pct', { ascending: false }).limit(5);
      if (brokerData) setTargets(brokerData);

      // 5. Daily Scans
      const { data: scanData } = await supabase.from('daily_scans').select('*').order('id', { ascending: true });
      if (scanData) setScans(scanData);
    }
    fetchData();
    const interval = setInterval(fetchData, 5000); // Live Refresh
    return () => clearInterval(interval);
  }, []);

  // --- FILTER LOGIC ---
  const filteredScans = scans.filter((item) => {
    const matchesSearch = item.symbol.toLowerCase().includes(search.toLowerCase());
    const matchesTrend = trendFilter === "ALL" || item.trend === trendFilter;
    return matchesSearch && matchesTrend;
  });

  // --- PAGINATION LOGIC ---
  const totalPages = Math.ceil(filteredScans.length / rowsPerPage);
  const paginatedScans = filteredScans.slice((page - 1) * rowsPerPage, page * rowsPerPage);

  return (
    <main className="bg-slate-950 min-h-screen text-white font-sans overflow-x-hidden">
      
      {/* 1. MARQUEE TICKER */}
      <div className="w-full bg-blue-900/20 border-b border-blue-900/50 overflow-hidden whitespace-nowrap py-2">
        <div className="inline-block animate-marquee">
            {indices.map((idx) => (
                <span key={idx.symbol} className="mx-6 font-mono text-sm">
                    <span className="font-bold text-slate-300">{idx.symbol}:</span> 
                    <span className="ml-2 font-bold">₹{idx.price}</span>
                    <span className={`ml-2 ${idx.percent_change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        ({idx.percent_change > 0 ? '+' : ''}{idx.percent_change}%)
                    </span>
                </span>
            ))}
        </div>
      </div>

      <div className="p-4 md:p-10 max-w-7xl mx-auto">
        
        {/* 2. HEADER */}
        <div className="mb-8 flex flex-col md:flex-row justify-between items-end border-b border-slate-800 pb-6">
            <Link href="/" className="cursor-pointer">
                <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">
                    StockCal Pro
                </h1>
                <p className="text-slate-400 mt-2 text-sm uppercase tracking-widest">Institutional Intelligence for Retail Traders</p>
            </Link>
        </div>

        {/* 3. LIVE BOT TRADES */}
        <Card className="bg-slate-900/50 border border-slate-800 mb-8 shadow-lg shadow-blue-900/10">
            <div className="flex items-center gap-3 mb-6">
                <BoltIcon className="h-6 w-6 text-yellow-400 animate-pulse" />
                <Title className="text-white">Live Bot Executions</Title>
            </div>
            <Table>
                <TableHead>
                    <TableRow>
                        <TableHeaderCell className="text-slate-400">Stock</TableHeaderCell>
                        <TableHeaderCell className="text-slate-400 text-right">Price</TableHeaderCell>
                        <TableHeaderCell className="text-slate-400 text-right">Qty</TableHeaderCell>
                        <TableHeaderCell className="text-slate-400 text-center">Status</TableHeaderCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    {trades.length === 0 ? (
                        <TableRow>
                            <TableCell colSpan={4} className="text-center text-slate-500 py-4">Waiting for execution...</TableCell>
                        </TableRow>
                    ) : (
                        trades.slice(0, 5).map((item) => (
                            <TableRow key={item.id} className="hover:bg-slate-800/30">
                                <TableCell className="text-white font-bold">{item.symbol.replace('.NS','')}</TableCell>
                                <TableCell className="text-right font-mono text-emerald-400">₹{item.buy_price}</TableCell>
                                <TableCell className="text-right text-slate-400">{item.quantity}</TableCell>
                                <TableCell className="text-center"><Badge size="xs" color="emerald">{item.status}</Badge></TableCell>
                            </TableRow>
                        ))
                    )}
                </TableBody>
            </Table>
        </Card>

        {/* 4. DAILY ALGO SCANNER (UPGRADED) */}
        <Card className="bg-slate-900/50 border border-slate-800 mb-8">
            <div className="flex flex-col md:flex-row justify-between items-center mb-6 gap-4">
                <div className="flex items-center gap-3">
                    <CalculatorIcon className="h-6 w-6 text-purple-400" />
                    <Title className="text-white">Daily Algo Scanner</Title>
                </div>
                
                {/* FILTERS */}
                <div className="flex gap-2 w-full md:w-auto">
                    <div className="relative w-full md:w-48">
                        <TextInput 
                            icon={MagnifyingGlassIcon} 
                            placeholder="Search Stock..." 
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                        />
                    </div>
                    <Select value={trendFilter} onValueChange={setTrendFilter} className="w-full md:w-32">
                        <SelectItem value="ALL">All Trends</SelectItem>
                        <SelectItem value="UP">Uptrend</SelectItem>
                        <SelectItem value="DOWN">Downtrend</SelectItem>
                    </Select>
                </div>
            </div>

            <Table>
                <TableHead>
                    <TableRow>
                        <TableHeaderCell className="text-slate-400">Stock</TableHeaderCell>
                        <TableHeaderCell className="text-slate-400 text-right">Price</TableHeaderCell>
                        <TableHeaderCell className="text-slate-400 text-center">Trend</TableHeaderCell>
                        <TableHeaderCell className="text-slate-400 text-right">RSI</TableHeaderCell>
                        <TableHeaderCell className="text-slate-400">Condition</TableHeaderCell>
                        <TableHeaderCell className="text-slate-400 text-center">Signal</TableHeaderCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    {paginatedScans.map((item) => (
                        <TableRow key={item.id} className="hover:bg-slate-800/40">
                            <TableCell className="text-white font-bold">{item.symbol.replace('.NS','')}</TableCell>
                            <TableCell className="text-right font-mono text-slate-300">₹{item.price}</TableCell>
                            <TableCell className="text-center">
                                <Badge size="xs" color={item.trend === 'UP' ? 'emerald' : 'rose'}>{item.trend}</Badge>
                            </TableCell>
                            <TableCell className="text-right font-mono text-slate-400">{item.rsi}</TableCell>
                            <TableCell className="text-slate-300">{item.condition}</TableCell>
                            <TableCell className="text-center">
                                <Badge size="sm" color={item.signal === 'BUY' ? 'emerald' : (item.signal === 'SELL' ? 'rose' : 'gray')}>
                                    {item.signal}
                                </Badge>
                            </TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>

            {/* PAGINATION */}
            <div className="flex justify-between items-center mt-4 border-t border-slate-800 pt-4 px-2">
                <Text className="text-xs text-slate-500">
                    Page {page} of {totalPages || 1}
                </Text>
                <div className="flex gap-2">
                    <button 
                        disabled={page === 1}
                        onClick={() => setPage(p => p - 1)}
                        className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-white text-xs rounded disabled:opacity-30 transition-colors"
                    >
                        Previous
                    </button>
                    <button 
                        disabled={page >= totalPages}
                        onClick={() => setPage(p => p + 1)}
                        className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-white text-xs rounded disabled:opacity-30 transition-colors"
                    >
                        Next
                    </button>
                </div>
            </div>
        </Card>

        {/* 5. GRID FOR TARGETS & NEWS */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* ANALYST TARGETS */}
            <div className="lg:col-span-1 flex flex-col">
                <div className="flex items-center gap-2 mb-4">
                    <ArrowTrendingUpIcon className="h-5 w-5 text-emerald-500" />
                    <h2 className="text-xl text-white font-bold">Analyst Top Picks</h2>
                </div>
                <Card className="bg-slate-900/50 border border-slate-800 flex-grow">
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableHeaderCell className="text-slate-400 text-xs uppercase">Stock</TableHeaderCell>
                                <TableHeaderCell className="text-slate-400 text-xs uppercase text-right">Target</TableHeaderCell>
                                <TableHeaderCell className="text-slate-400 text-xs uppercase text-right">Upside</TableHeaderCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {targets.map((item) => (
                                <TableRow key={item.id} className="hover:bg-slate-800/40">
                                    <TableCell className="text-white font-bold">{item.symbol.replace('.NS','')}</TableCell>
                                    <TableCell className="text-right text-slate-400">₹{item.target_mean}</TableCell>
                                    <TableCell className="text-right text-emerald-400 font-bold">+{item.upside_pct}%</TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </Card>
            </div>

            {/* NEWS FEED */}
            <div className="lg:col-span-2">
                <div className="flex items-center gap-2 mb-4">
                    <NewspaperIcon className="h-5 w-5 text-blue-500" />
                    <h2 className="text-xl text-white font-bold">Market Intelligence</h2>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {articles.map((article) => (
                        <Link key={article.id} href={`/news/${article.slug}`} className="block h-full group">
                            <Card className="bg-slate-900 border-slate-800 hover:border-blue-500/50 cursor-pointer h-full transition-all hover:shadow-lg hover:shadow-blue-900/10 relative overflow-hidden">
                                <div className="absolute top-0 left-0 w-1 h-full bg-blue-600 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                                <div className="pl-2">
                                    <div className="flex justify-between items-start mb-3">
                                        <Badge size="xs" color="slate">{new Date(article.published_at).toLocaleDateString()}</Badge>
                                        <span className="text-xs font-bold text-slate-500 tracking-wider">{article.symbol.replace('.NS','')}</span>
                                    </div>
                                    <Title className="text-white text-md font-bold leading-snug mb-4 group-hover:text-blue-400 transition-colors">
                                        {article.title}
                                    </Title>
                                    <Text className="text-blue-500 text-xs font-medium flex items-center gap-1">
                                        Read Analysis <span className="group-hover:translate-x-1 transition-transform">&rarr;</span>
                                    </Text>
                                </div>
                            </Card>
                        </Link>
                    ))}
                </div>
            </div>
        </div>

      </div>
    </main>
  );
}