'use client';
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronRight, ChevronLeft, Target, Users, Lightbulb } from 'lucide-react';

// --- MOCK DATA (Fallback if no real data is passed) ---
const defaultProfile = {
  ticker: "HINDALCO",
  name: "Hindalco Industries",
  about: {
    title: "The Metals Powerhouse",
    text: "The world's largest aluminium rolling company and a major copper player. A flagship company of the Aditya Birla Group.",
    products: ["Aluminium Value-Added", "Copper Rods", "Specialty Alumina"],
    global_presence: "Operations in 10 countries"
  },
  goals: {
    title: "Strategic Vision 2030",
    text: "Transitioning from a 'Metals' company to a 'Materials' solution provider.",
    points: [
      "Invest ₹2,000 Cr in EV Battery Foil plant.",
      "Achieve Net Zero Carbon by 2050.",
      "Reduce debt by $1B in FY26."
    ]
  },
  people: {
    ceo: "Satish Pai",
    ceo_quote: "We are entering a phase of organic growth with a focus on downstream value addition.",
    workforce: "40,000+ Employees"
  }
};

// --- FIX: Define the Prop Type ---
interface BusinessFlipbookProps {
  data?: any; // We accept 'data' as an optional prop
}

export default function BusinessFlipbook({ data }: BusinessFlipbookProps) {
  const [slide, setSlide] = useState(0);
  const totalSlides = 3;

  // --- FIX: Use passed data OR fallback to default ---
  const stockProfile = data || defaultProfile;

  const nextSlide = () => setSlide((prev) => (prev + 1) % totalSlides);
  const prevSlide = () => setSlide((prev) => (prev - 1 + totalSlides) % totalSlides);

  return (
    <div className="w-full max-w-5xl mx-auto h-[500px] bg-[#0F1115] border border-slate-800 rounded-2xl overflow-hidden shadow-2xl flex flex-col md:flex-row">
      
      {/* LEFT: Cover Image & Nav */}
      <div className="w-full md:w-1/3 bg-gradient-to-br from-indigo-900 to-slate-900 p-8 flex flex-col justify-between relative overflow-hidden">
         {/* Decorative Background */}
         <div className="absolute top-0 left-0 w-full h-full opacity-10 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')]"></div>
         
         <div className="z-10">
            <h1 className="text-4xl font-black text-white tracking-tighter mb-2">{stockProfile.ticker}</h1>
            <span className="inline-block px-3 py-1 bg-white/10 backdrop-blur-md rounded-full text-xs font-bold text-white uppercase tracking-widest">
               Annual Report Highlights
            </span>
         </div>

         <div className="z-10 flex gap-4 mt-8">
            <button onClick={prevSlide} className="p-3 bg-black/20 hover:bg-black/40 rounded-full text-white transition-all"><ChevronLeft className="w-5 h-5"/></button>
            <button onClick={nextSlide} className="flex-1 px-4 py-3 bg-white text-indigo-900 rounded-full font-bold text-sm flex items-center justify-center gap-2 hover:bg-indigo-50 transition-all">
               Next Page <ChevronRight className="w-4 h-4"/>
            </button>
         </div>
      </div>

      {/* RIGHT: The Content Pages */}
      <div className="flex-1 bg-[#0F1115] relative p-8 md:p-12">
        <AnimatePresence mode="wait">
          
          {/* PAGE 1: BUSINESS PROFILE */}
          {slide === 0 && (
            <motion.div key="p1" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="h-full flex flex-col justify-center">
               <Lightbulb className="w-10 h-10 text-amber-400 mb-6" />
               <h2 className="text-2xl font-bold text-white mb-4">What they do</h2>
               <p className="text-slate-400 text-lg leading-relaxed mb-6">{stockProfile.about?.text || "No description available."}</p>
               
               <div className="grid grid-cols-2 gap-4">
                  {stockProfile.about?.products?.map((p: string, i: number) => (
                     <div key={i} className="flex items-center gap-2 text-sm text-slate-300 font-medium">
                        <div className="w-1.5 h-1.5 bg-indigo-500 rounded-full"></div> {p}
                     </div>
                  ))}
               </div>
            </motion.div>
          )}

          {/* PAGE 2: GOALS & VISION */}
          {slide === 1 && (
            <motion.div key="p2" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="h-full flex flex-col justify-center">
               <Target className="w-10 h-10 text-rose-500 mb-6" />
               <h2 className="text-2xl font-bold text-white mb-4">{stockProfile.goals?.title || "Future Goals"}</h2>
               <div className="space-y-4">
                  {stockProfile.goals?.points?.map((g: string, i: number) => (
                     <div key={i} className="bg-slate-900/50 p-4 rounded-xl border border-slate-800 flex gap-3">
                        <span className="text-rose-500 font-bold font-mono">0{i+1}</span>
                        <span className="text-slate-300 text-sm">{g}</span>
                     </div>
                  ))}
               </div>
            </motion.div>
          )}

          {/* PAGE 3: PEOPLE & CULTURE */}
          {slide === 2 && (
            <motion.div key="p3" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="h-full flex flex-col justify-center">
               <Users className="w-10 h-10 text-emerald-500 mb-6" />
               <h2 className="text-2xl font-bold text-white mb-2">Leadership View</h2>
               <div className="relative bg-slate-800/50 p-6 rounded-xl border-l-4 border-emerald-500 my-4">
                  <p className="text-slate-200 italic font-serif text-lg">"{stockProfile.people?.ceo_quote || "Leadership focused on growth."}"</p>
                  <div className="mt-4 flex items-center gap-2">
                     <div className="w-8 h-8 bg-slate-600 rounded-full"></div> 
                     <div>
                        <div className="text-xs font-bold text-white">{stockProfile.people?.ceo || "CEO"}</div>
                        <div className="text-[10px] text-slate-500 uppercase">Managing Director</div>
                     </div>
                  </div>
               </div>
            </motion.div>
          )}

        </AnimatePresence>

        {/* Page Indicator */}
        <div className="absolute bottom-6 right-8 text-xs text-slate-600 font-mono">
           PAGE 0{slide + 1} / 0{totalSlides}
        </div>
      </div>
    </div>
  );
}