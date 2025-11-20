"use client";

import { useRouter } from "next/navigation";
import { SearchBar } from "@/components/search/SearchBar";

/**
 * Search Page
 *
 * Main search interface with autocomplete functionality.
 * This is a Client Component due to event handlers (onSearch).
 *
 * Features:
 * - Autocomplete-enabled search bar
 * - Clean, minimal layout with poker theme
 * - Responsive design (mobile/desktop)
 * - Proper spacing and typography
 * - Navigation to results page on search
 *
 * @route /search
 */
export default function SearchPage() {
  const router = useRouter();

  const handleSearch = (query: string) => {
    if (query.trim()) {
      // Navigate to results page with search query
      const encoded = encodeURIComponent(query);
      router.push(`/search/results?q=${encoded}`);
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      {/* Header Section */}
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Logo/Title Area */}
          <div className="text-center mb-12 pt-12">
            <h1 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-poker-chip-red via-poker-chip-purple to-poker-chip-green bg-clip-text text-transparent">
              Poker Archive Search
            </h1>
            <p className="text-lg text-muted-foreground">
              Search poker hands, players, and strategies with intelligent autocomplete
            </p>
          </div>

          {/* Search Bar Section */}
          <div className="mb-8">
            <SearchBar
              initialQuery=""
              onSearch={handleSearch}
              enableAutocomplete={true}
              placeholder="Search poker hands, players, tags..."
            />
          </div>

          {/* Helper Text */}
          <div className="text-center mt-6">
            <p className="text-sm text-muted-foreground">
              Try searching for:{" "}
              <span className="text-foreground font-medium">hero call</span>,{" "}
              <span className="text-foreground font-medium">junglemann</span>, or{" "}
              <span className="text-foreground font-medium">WSOP 2024</span>
            </p>
          </div>
        </div>
      </div>

      {/* Features Section (Optional - shows when no search) */}
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-4xl mx-auto">
          <div className="grid md:grid-cols-3 gap-6">
            {/* Feature 1: Autocomplete */}
            <div className="p-6 rounded-lg bg-card border border-border hover:border-poker-chip-green transition-colors">
              <div className="w-12 h-12 rounded-full bg-poker-chip-green/10 flex items-center justify-center mb-4">
                <svg
                  className="w-6 h-6 text-poker-chip-green"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 10V3L4 14h7v7l9-11h-7z"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-semibold mb-2">Smart Autocomplete</h3>
              <p className="text-sm text-muted-foreground">
                Get instant suggestions as you type, powered by advanced search algorithms
              </p>
            </div>

            {/* Feature 2: Advanced Search */}
            <div className="p-6 rounded-lg bg-card border border-border hover:border-poker-chip-purple transition-colors">
              <div className="w-12 h-12 rounded-full bg-poker-chip-purple/10 flex items-center justify-center mb-4">
                <svg
                  className="w-6 h-6 text-poker-chip-purple"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-semibold mb-2">Advanced Filters</h3>
              <p className="text-sm text-muted-foreground">
                Filter by pot size, tournament, tags, and more for precise results
              </p>
            </div>

            {/* Feature 3: Video Integration */}
            <div className="p-6 rounded-lg bg-card border border-border hover:border-poker-chip-red transition-colors">
              <div className="w-12 h-12 rounded-full bg-poker-chip-red/10 flex items-center justify-center mb-4">
                <svg
                  className="w-6 h-6 text-poker-chip-red"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-semibold mb-2">Video Archive</h3>
              <p className="text-sm text-muted-foreground">
                Watch hand replays with timestamped video clips from tournaments
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="container mx-auto px-4 py-8 mt-auto">
        <div className="max-w-4xl mx-auto text-center text-sm text-muted-foreground">
          <p>
            Powered by Vertex AI Vector Search • Built with Next.js 15 & TypeScript
          </p>
        </div>
      </footer>
    </main>
  );
}
