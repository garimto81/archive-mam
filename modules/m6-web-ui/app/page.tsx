/**
 * Home Page
 * Landing page with search bar and featured hands
 */

'use client';

import { useRouter } from 'next/navigation';
import { SearchBar } from '@/components/SearchBar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Search, Download, Heart, TrendingUp } from 'lucide-react';

export default function HomePage() {
  const router = useRouter();

  const handleSearch = (query: string) => {
    router.push(`/search?q=${encodeURIComponent(query)}`);
  };

  return (
    <div className="container mx-auto px-4 py-12">
      {/* Hero section */}
      <div className="max-w-4xl mx-auto text-center mb-12">
        <h1 className="text-4xl font-bold tracking-tight sm:text-6xl mb-4">
          WSOP Archive Search
        </h1>
        <p className="text-lg text-muted-foreground mb-8">
          Search and download poker hand clips from World Series of Poker tournaments
        </p>

        {/* Search bar */}
        <SearchBar onSearch={handleSearch} autoFocus />
      </div>

      {/* Feature cards */}
      <div className="max-w-5xl mx-auto grid gap-6 sm:grid-cols-2 lg:grid-cols-3 mb-12">
        <FeatureCard
          icon={<Search className="h-8 w-8 text-primary" />}
          title="Semantic Search"
          description="Natural language search powered by AI - find hands by describing the action"
        />
        <FeatureCard
          icon={<Download className="h-8 w-8 text-primary" />}
          title="Clip Download"
          description="Download high-quality video clips of any hand with precise timecode"
        />
        <FeatureCard
          icon={<Heart className="h-8 w-8 text-primary" />}
          title="Favorites"
          description="Save your favorite hands and build your own collection"
        />
      </div>

      {/* Quick search suggestions */}
      <div className="max-w-4xl mx-auto">
        <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
          <TrendingUp className="h-6 w-6" />
          Popular Searches
        </h2>
        <div className="flex flex-wrap gap-2">
          <SearchSuggestion query="Tom Dwan bluff" onClick={handleSearch} />
          <SearchSuggestion query="AA vs KK all-in" onClick={handleSearch} />
          <SearchSuggestion query="Phil Ivey fold" onClick={handleSearch} />
          <SearchSuggestion query="massive pot" onClick={handleSearch} />
          <SearchSuggestion query="river suckout" onClick={handleSearch} />
          <SearchSuggestion query="Daniel Negreanu" onClick={handleSearch} />
          <SearchSuggestion query="final table 2024" onClick={handleSearch} />
          <SearchSuggestion query="pocket aces cracked" onClick={handleSearch} />
        </div>
      </div>

      {/* Stats section */}
      <div className="max-w-4xl mx-auto mt-12 grid gap-4 sm:grid-cols-3 text-center">
        <StatCard value="125,000+" label="Poker Hands" />
        <StatCard value="2,400+" label="Hours of Video" />
        <StatCard value="98.5%" label="Timecode Accuracy" />
      </div>
    </div>
  );
}

// Feature card component
function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <Card>
      <CardHeader>
        <div className="mb-2">{icon}</div>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <CardDescription>{description}</CardDescription>
      </CardContent>
    </Card>
  );
}

// Search suggestion badge
function SearchSuggestion({ query, onClick }: { query: string; onClick: (query: string) => void }) {
  return (
    <Badge
      variant="outline"
      className="cursor-pointer hover:bg-accent transition-colors"
      onClick={() => onClick(query)}
    >
      {query}
    </Badge>
  );
}

// Stat card component
function StatCard({ value, label }: { value: string; label: string }) {
  return (
    <div>
      <div className="text-3xl font-bold text-primary">{value}</div>
      <div className="text-sm text-muted-foreground">{label}</div>
    </div>
  );
}
