/**
 * Empty State Component Tests
 *
 * Test suite for the EmptyState component covering:
 * - Empty state messaging
 * - Suggestions display
 * - Example searches
 * - Clear filters functionality
 * - Accessibility
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { EmptyState } from "./EmptyState";

describe("EmptyState Component", () => {
  describe("Rendering", () => {
    it("renders with required props", () => {
      render(<EmptyState query="test query" />);

      expect(screen.getByRole("status")).toBeInTheDocument();
      expect(screen.getByText("No results found")).toBeInTheDocument();
      expect(screen.getByText(/we couldn't find any poker hands/i)).toBeInTheDocument();
    });

    it("displays the search query", () => {
      const query = "hero call river";
      render(<EmptyState query={query} />);

      expect(screen.getByText(`"${query}"`)).toBeInTheDocument();
    });

    it("renders search icon", () => {
      const { container } = render(<EmptyState query="test" />);

      // Check for icon container with search-like styling
      const icon = container.querySelector(".inline-flex.items-center.justify-center");
      expect(icon).toBeInTheDocument();
    });
  });

  describe("Suggestions", () => {
    it("displays default suggestions if not provided", () => {
      render(<EmptyState query="test" />);

      expect(screen.getByText("Suggestions:")).toBeInTheDocument();
      expect(screen.getByText(/try using different keywords/i)).toBeInTheDocument();
      expect(screen.getByText(/check your spelling/i)).toBeInTheDocument();
    });

    it("displays custom suggestions when provided", () => {
      const suggestions = ["Suggestion 1", "Suggestion 2", "Custom Suggestion"];

      render(
        <EmptyState
          query="test"
          suggestions={suggestions}
        />
      );

      suggestions.forEach((suggestion) => {
        expect(screen.getByText(suggestion)).toBeInTheDocument();
      });
    });

    it("shows filter-related suggestion when hasActiveFilters is true", () => {
      render(
        <EmptyState
          query="test"
          hasActiveFilters={true}
        />
      );

      expect(screen.getByText(/try removing some filters/i)).toBeInTheDocument();
    });

    it("shows search criteria suggestion when hasActiveFilters is false", () => {
      render(
        <EmptyState
          query="test"
          hasActiveFilters={false}
        />
      );

      expect(screen.getByText(/try adjusting your search criteria/i)).toBeInTheDocument();
    });
  });

  describe("Clear Filters Button", () => {
    it("displays clear filters button when hasActiveFilters is true", () => {
      render(
        <EmptyState
          query="test"
          hasActiveFilters={true}
          onClearFilters={jest.fn()}
        />
      );

      expect(screen.getByRole("button", { name: /clear filters/i })).toBeInTheDocument();
    });

    it("hides clear filters button when hasActiveFilters is false", () => {
      render(
        <EmptyState
          query="test"
          hasActiveFilters={false}
        />
      );

      expect(screen.queryByRole("button", { name: /clear filters/i })).not.toBeInTheDocument();
    });

    it("calls onClearFilters when button is clicked", async () => {
      const user = userEvent.setup();
      const handleClearFilters = jest.fn();

      render(
        <EmptyState
          query="test"
          hasActiveFilters={true}
          onClearFilters={handleClearFilters}
        />
      );

      const button = screen.getByRole("button", { name: /clear filters/i });
      await user.click(button);

      expect(handleClearFilters).toHaveBeenCalledTimes(1);
    });
  });

  describe("Example Searches", () => {
    it("displays example search section", () => {
      render(<EmptyState query="test" />);

      expect(screen.getByText(/or try searching for/i)).toBeInTheDocument();
    });

    it("displays example search buttons", () => {
      render(<EmptyState query="test" />);

      expect(screen.getByRole("button", { name: /river call bluff/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /hero fold hero call/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /high pot all-in/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /final table heads up/i })).toBeInTheDocument();
    });

    it("calls onExampleSearch with selected example", async () => {
      const user = userEvent.setup();
      const handleExampleSearch = jest.fn();

      render(
        <EmptyState
          query="test"
          onExampleSearch={handleExampleSearch}
        />
      );

      const exampleButton = screen.getByRole("button", { name: /river call bluff/i });
      await user.click(exampleButton);

      expect(handleExampleSearch).toHaveBeenCalledWith("river call bluff");
    });

    it("all example buttons have proper ARIA labels", () => {
      render(<EmptyState query="test" />);

      const examples = ["river call bluff", "hero fold hero call", "high pot all-in", "final table heads up"];

      examples.forEach((example) => {
        const button = screen.getByRole("button", { name: new RegExp(example, "i") });
        expect(button).toHaveAttribute("aria-label", `Search for ${example}`);
      });
    });
  });

  describe("Accessibility", () => {
    it("has status role for live region", () => {
      render(<EmptyState query="test" />);

      expect(screen.getByRole("status")).toBeInTheDocument();
    });

    it("status region has aria-live polite", () => {
      render(<EmptyState query="test" />);

      const status = screen.getByRole("status");
      expect(status).toHaveAttribute("aria-live", "polite");
    });

    it("buttons are keyboard accessible", async () => {
      const user = userEvent.setup();
      const handleClearFilters = jest.fn();

      render(
        <EmptyState
          query="test"
          hasActiveFilters={true}
          onClearFilters={handleClearFilters}
        />
      );

      const button = screen.getByRole("button", { name: /clear filters/i });
      button.focus();
      expect(button).toHaveFocus();

      await user.keyboard("{Enter}");
      expect(handleClearFilters).toHaveBeenCalled();
    });

    it("icon is properly hidden from screen readers", () => {
      const { container } = render(<EmptyState query="test" />);

      // SVG icons should be aria-hidden or not announced
      const svg = container.querySelector("svg");
      if (svg) {
        expect(svg).toHaveAttribute("aria-hidden", "true");
      }
    });

    it("has proper heading hierarchy", () => {
      render(<EmptyState query="test" />);

      const heading = screen.getByRole("heading", { level: 2 });
      expect(heading).toHaveTextContent("No results found");
    });
  });

  describe("Styling", () => {
    it("applies custom className", () => {
      const { container } = render(
        <EmptyState query="test" className="custom-class" />
      );

      const mainDiv = container.firstChild;
      expect(mainDiv).toHaveClass("custom-class");
    });

    it("renders centered layout", () => {
      const { container } = render(<EmptyState query="test" />);

      const mainDiv = container.firstChild;
      expect(mainDiv).toHaveClass("flex", "flex-col", "items-center", "justify-center");
    });

    it("renders with responsive spacing", () => {
      const { container } = render(<EmptyState query="test" />);

      const mainDiv = container.firstChild;
      expect(mainDiv).toHaveClass("py-12", "sm:py-16");
      expect(mainDiv).toHaveClass("px-4", "sm:px-6");
    });
  });

  describe("Content Layout", () => {
    it("renders elements in correct order", () => {
      const { container } = render(<EmptyState query="test" />);

      const children = container.querySelector(".flex.flex-col")?.children;
      expect(children?.[0]).toHaveClass("mb-6"); // Icon
      expect(children?.[1]).toHaveClass("text-2xl"); // "No results found"
    });

    it("displays help text", () => {
      render(<EmptyState query="test" />);

      expect(screen.getByText(/need help\?/i)).toBeInTheDocument();
      expect(screen.getByText(/keyboard shortcuts/i)).toBeInTheDocument();
    });

    it("shows keyboard hint with proper styling", () => {
      const { container } = render(<EmptyState query="test" />);

      // Check for the keyboard hint (?)
      const hintSpan = container.querySelector(
        "span.inline-block.px-1\\.5.py-0\\.5.rounded.bg-muted"
      );
      expect(hintSpan).toBeInTheDocument();
      expect(hintSpan).toHaveTextContent("?");
    });
  });

  describe("Responsive Design", () => {
    it("has responsive padding classes", () => {
      const { container } = render(<EmptyState query="test" />);

      const mainDiv = container.firstChild;
      expect(mainDiv).toHaveClass("py-12", "sm:py-16");
      expect(mainDiv).toHaveClass("px-4", "sm:px-6");
    });

    it("example buttons are responsive", () => {
      const { container } = render(<EmptyState query="test" />);

      // Look for grid with responsive columns
      const grid = container.querySelector(".grid.grid-cols-1");
      expect(grid).toHaveClass("sm:grid-cols-2");
    });
  });

  describe("Integration", () => {
    it("works with all props together", async () => {
      const user = userEvent.setup();
      const handleClearFilters = jest.fn();
      const handleExampleSearch = jest.fn();

      const suggestions = ["Custom suggestion 1", "Custom suggestion 2"];

      render(
        <EmptyState
          query="complex query"
          suggestions={suggestions}
          hasActiveFilters={true}
          onClearFilters={handleClearFilters}
          onExampleSearch={handleExampleSearch}
          className="test-class"
        />
      );

      // Check content
      expect(screen.getByText('"complex query"')).toBeInTheDocument();
      suggestions.forEach((s) => expect(screen.getByText(s)).toBeInTheDocument());

      // Test interactions
      const clearButton = screen.getByRole("button", { name: /clear filters/i });
      await user.click(clearButton);
      expect(handleClearFilters).toHaveBeenCalled();

      const exampleButton = screen.getByRole("button", { name: /river call bluff/i });
      await user.click(exampleButton);
      expect(handleExampleSearch).toHaveBeenCalledWith("river call bluff");
    });
  });
});
