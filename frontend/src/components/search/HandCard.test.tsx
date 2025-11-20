/**
 * HandCard Component Tests
 *
 * Tests for search result hand card component with status tracking
 */

import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import "@testing-library/jest-dom";
import { HandCard } from "./HandCard";
import type { SearchResultItem } from "@/types/search";

// Mock child components
vi.mock("@/components/video/VideoPreviewThumbnail", () => ({
  VideoPreviewThumbnail: ({ handId }: { handId: string }) => (
    <div data-testid="video-preview">{handId}</div>
  ),
}));

vi.mock("@/components/status/StatusBadge", () => ({
  StatusBadge: ({ status, progress, error, compact }: any) => (
    <div data-testid="status-badge" data-status={status} data-progress={progress} data-error={error} data-compact={compact}>
      {status}
    </div>
  ),
}));

vi.mock("@/components/status/ProgressBar", () => ({
  ProgressBar: ({ value, variant, size, animated }: any) => (
    <div data-testid="progress-bar" data-value={value} data-variant={variant} data-size={size} data-animated={animated}>
      {value}%
    </div>
  ),
}));

// Mock data
const mockResult: SearchResultItem = {
  handId: "wsop_2023_hand_0001",
  score: 0.92,
  hero_name: "Phil Ivey",
  villain_name: "Tom Dwan",
  pot_bb: 145.5,
  street: "RIVER",
  result: "WIN",
  tags: ["BLUFF", "HERO_CALL", "HIGH_STAKES"],
  thumbnail_url: "https://example.com/thumb.jpg",
  videoUrl: "https://example.com/video.mp4",
  durationSeconds: 120,
};

describe("HandCard", () => {
  describe("Basic Rendering", () => {
    it("renders with correct hand data", () => {
      render(<HandCard result={mockResult} />);

      expect(screen.getByText("Phil Ivey")).toBeInTheDocument();
      expect(screen.getByText("Tom Dwan")).toBeInTheDocument();
      expect(screen.getByText("145.5bb")).toBeInTheDocument();
      expect(screen.getByText("RIVER")).toBeInTheDocument();
    });

    it("renders video preview thumbnail", () => {
      render(<HandCard result={mockResult} />);

      const videoPreview = screen.getByTestId("video-preview");
      expect(videoPreview).toBeInTheDocument();
      expect(videoPreview).toHaveTextContent("wsop_2023_hand_0001");
    });

    it("renders relevance score badge", () => {
      render(<HandCard result={mockResult} />);

      expect(screen.getByText("92%")).toBeInTheDocument();
    });

    it("renders result indicator badge", () => {
      render(<HandCard result={mockResult} />);

      expect(screen.getByText("WIN")).toBeInTheDocument();
    });

    it("renders tags", () => {
      render(<HandCard result={mockResult} />);

      expect(screen.getByText("BLUFF")).toBeInTheDocument();
      expect(screen.getByText("HERO_CALL")).toBeInTheDocument();
      expect(screen.getByText("HIGH_STAKES")).toBeInTheDocument();
    });

    it("shows +N badge when more than 3 tags", () => {
      const resultWithManyTags: SearchResultItem = {
        ...mockResult,
        tags: ["TAG1", "TAG2", "TAG3", "TAG4", "TAG5"],
      };

      render(<HandCard result={resultWithManyTags} />);

      expect(screen.getByText("+2")).toBeInTheDocument();
    });
  });

  describe("Click Handling", () => {
    it("calls onClick when card is clicked", () => {
      const handleClick = vi.fn();
      render(<HandCard result={mockResult} onClick={handleClick} />);

      const card = screen.getByRole("button");
      fireEvent.click(card);

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it("calls onClick when Enter key is pressed", () => {
      const handleClick = vi.fn();
      render(<HandCard result={mockResult} onClick={handleClick} />);

      const card = screen.getByRole("button");
      fireEvent.keyDown(card, { key: "Enter" });

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it("calls onClick when Space key is pressed", () => {
      const handleClick = vi.fn();
      render(<HandCard result={mockResult} onClick={handleClick} />);

      const card = screen.getByRole("button");
      fireEvent.keyDown(card, { key: " " });

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it("does not crash when onClick is not provided", () => {
      render(<HandCard result={mockResult} />);

      const card = screen.getByRole("button");
      fireEvent.click(card);

      // Should not throw error
      expect(card).toBeInTheDocument();
    });
  });

  describe("Status Badge Integration", () => {
    it("renders StatusBadge when analysisStatus is provided", () => {
      const resultWithStatus: SearchResultItem = {
        ...mockResult,
        analysisStatus: "completed",
      };

      render(<HandCard result={resultWithStatus} />);

      const statusBadge = screen.getByTestId("status-badge");
      expect(statusBadge).toBeInTheDocument();
      expect(statusBadge).toHaveAttribute("data-status", "completed");
    });

    it("does not render StatusBadge when analysisStatus is not provided", () => {
      render(<HandCard result={mockResult} />);

      expect(screen.queryByTestId("status-badge")).not.toBeInTheDocument();
    });

    it("passes compact=true to StatusBadge", () => {
      const resultWithStatus: SearchResultItem = {
        ...mockResult,
        analysisStatus: "processing",
      };

      render(<HandCard result={resultWithStatus} />);

      const statusBadge = screen.getByTestId("status-badge");
      expect(statusBadge).toHaveAttribute("data-compact", "true");
    });

    it("passes progress to StatusBadge when provided", () => {
      const resultWithProgress: SearchResultItem = {
        ...mockResult,
        analysisStatus: "processing",
        analysisProgress: 45,
      };

      render(<HandCard result={resultWithProgress} />);

      const statusBadge = screen.getByTestId("status-badge");
      expect(statusBadge).toHaveAttribute("data-progress", "45");
    });

    it("passes error to StatusBadge when provided", () => {
      const resultWithError: SearchResultItem = {
        ...mockResult,
        analysisStatus: "failed",
        analysisError: "Analysis timeout",
      };

      render(<HandCard result={resultWithError} />);

      const statusBadge = screen.getByTestId("status-badge");
      expect(statusBadge).toHaveAttribute("data-error", "Analysis timeout");
    });

    it("renders all status types correctly", () => {
      const statuses: Array<"completed" | "processing" | "pending" | "failed"> = [
        "completed",
        "processing",
        "pending",
        "failed",
      ];

      statuses.forEach((status) => {
        const { rerender } = render(
          <HandCard result={{ ...mockResult, analysisStatus: status }} />
        );

        const statusBadge = screen.getByTestId("status-badge");
        expect(statusBadge).toHaveAttribute("data-status", status);

        rerender(<div />);
      });
    });
  });

  describe("ProgressBar Integration", () => {
    it("renders ProgressBar when status is processing and progress is provided", () => {
      const resultWithProgress: SearchResultItem = {
        ...mockResult,
        analysisStatus: "processing",
        analysisProgress: 60,
      };

      render(<HandCard result={resultWithProgress} />);

      const progressBar = screen.getByTestId("progress-bar");
      expect(progressBar).toBeInTheDocument();
      expect(progressBar).toHaveAttribute("data-value", "60");
    });

    it("does not render ProgressBar when status is not processing", () => {
      const resultCompleted: SearchResultItem = {
        ...mockResult,
        analysisStatus: "completed",
        analysisProgress: 100,
      };

      render(<HandCard result={resultCompleted} />);

      expect(screen.queryByTestId("progress-bar")).not.toBeInTheDocument();
    });

    it("does not render ProgressBar when progress is not provided", () => {
      const resultNoProgress: SearchResultItem = {
        ...mockResult,
        analysisStatus: "processing",
      };

      render(<HandCard result={resultNoProgress} />);

      expect(screen.queryByTestId("progress-bar")).not.toBeInTheDocument();
    });

    it("passes correct props to ProgressBar", () => {
      const resultWithProgress: SearchResultItem = {
        ...mockResult,
        analysisStatus: "processing",
        analysisProgress: 75,
      };

      render(<HandCard result={resultWithProgress} />);

      const progressBar = screen.getByTestId("progress-bar");
      expect(progressBar).toHaveAttribute("data-value", "75");
      expect(progressBar).toHaveAttribute("data-variant", "processing");
      expect(progressBar).toHaveAttribute("data-size", "sm");
      expect(progressBar).toHaveAttribute("data-animated", "true");
    });

    it("renders both StatusBadge and ProgressBar when processing", () => {
      const resultProcessing: SearchResultItem = {
        ...mockResult,
        analysisStatus: "processing",
        analysisProgress: 50,
      };

      render(<HandCard result={resultProcessing} />);

      expect(screen.getByTestId("status-badge")).toBeInTheDocument();
      expect(screen.getByTestId("progress-bar")).toBeInTheDocument();
    });
  });

  describe("Accessibility", () => {
    it("has role='button'", () => {
      render(<HandCard result={mockResult} />);

      const card = screen.getByRole("button");
      expect(card).toBeInTheDocument();
    });

    it("has tabIndex=0 for keyboard navigation", () => {
      render(<HandCard result={mockResult} />);

      const card = screen.getByRole("button");
      expect(card).toHaveAttribute("tabIndex", "0");
    });

    it("has descriptive aria-label", () => {
      render(<HandCard result={mockResult} />);

      const card = screen.getByRole("button");
      expect(card).toHaveAccessibleName(/Hand.*Phil Ivey.*Tom Dwan/);
    });

    it("has data-testid attributes for testing", () => {
      render(<HandCard result={mockResult} />);

      expect(screen.getByTestId("hand-card")).toBeInTheDocument();
      expect(screen.getByTestId("hand-thumbnail")).toBeInTheDocument();
      expect(screen.getByTestId("hand-metadata")).toBeInTheDocument();
    });
  });

  describe("Styling and Layout", () => {
    it("applies custom className", () => {
      const { container } = render(
        <HandCard result={mockResult} className="custom-class" />
      );

      const card = container.querySelector(".custom-class");
      expect(card).toBeInTheDocument();
    });

    it("has hover effects", () => {
      render(<HandCard result={mockResult} />);

      const card = screen.getByRole("button");
      expect(card).toHaveClass("hover:border-poker-chip-green");
      expect(card).toHaveClass("hover:shadow-lg");
    });

    it("has focus ring", () => {
      render(<HandCard result={mockResult} />);

      const card = screen.getByRole("button");
      expect(card).toHaveClass("focus:outline-none");
      expect(card).toHaveClass("focus:ring-2");
      expect(card).toHaveClass("focus:ring-poker-chip-green");
    });
  });

  describe("Edge Cases", () => {
    it("handles missing pot_bb gracefully", () => {
      const resultNoPot = {
        ...mockResult,
        pot_bb: undefined,
      } as SearchResultItem;

      render(<HandCard result={resultNoPot} />);

      expect(screen.getByText("N/A")).toBeInTheDocument();
    });

    it("handles missing street gracefully", () => {
      const resultNoStreet = {
        ...mockResult,
        street: undefined,
      } as unknown as SearchResultItem;

      render(<HandCard result={resultNoStreet} />);

      expect(screen.getByText("N/A")).toBeInTheDocument();
    });

    it("handles empty tags array", () => {
      const resultNoTags: SearchResultItem = {
        ...mockResult,
        tags: [],
      };

      render(<HandCard result={resultNoTags} />);

      const card = screen.getByTestId("hand-card");
      expect(card).toBeInTheDocument();
      expect(screen.queryByText("TAG")).not.toBeInTheDocument();
    });

    it("handles undefined tags", () => {
      const resultUndefinedTags = {
        ...mockResult,
        tags: undefined,
      } as unknown as SearchResultItem;

      render(<HandCard result={resultUndefinedTags} />);

      const card = screen.getByTestId("hand-card");
      expect(card).toBeInTheDocument();
    });

    it("handles very long player names", () => {
      const resultLongNames: SearchResultItem = {
        ...mockResult,
        hero_name: "Very Long Player Name That Might Overflow",
        villain_name: "Another Very Long Player Name",
      };

      render(<HandCard result={resultLongNames} />);

      expect(screen.getByText("Very Long Player Name That Might Overflow")).toBeInTheDocument();
      expect(screen.getByText("Another Very Long Player Name")).toBeInTheDocument();
    });

    it("handles all combinations of status and progress", () => {
      const combinations = [
        { analysisStatus: "completed" as const, analysisProgress: 100 },
        { analysisStatus: "processing" as const, analysisProgress: 50 },
        { analysisStatus: "processing" as const, analysisProgress: undefined },
        { analysisStatus: "pending" as const, analysisProgress: undefined },
        { analysisStatus: "failed" as const, analysisProgress: 25, analysisError: "Error" },
      ];

      combinations.forEach((combo) => {
        const { rerender } = render(
          <HandCard result={{ ...mockResult, ...combo }} />
        );

        const card = screen.getByTestId("hand-card");
        expect(card).toBeInTheDocument();

        rerender(<div />);
      });
    });
  });
});
