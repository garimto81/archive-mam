/**
 * ProgressBar Component Tests
 *
 * Tests for progress bar component with all variants
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import {
  ProgressBar,
  CompletedProgressBar,
  ProcessingProgressBar,
  FailedProgressBar,
  CircularProgress,
} from "./ProgressBar";

describe("ProgressBar", () => {
  describe("Basic Rendering", () => {
    it("renders with correct progress value", () => {
      render(<ProgressBar value={50} />);

      const progressBar = screen.getByRole("progressbar");
      expect(progressBar).toBeInTheDocument();
      expect(progressBar).toHaveAttribute("aria-valuenow", "50");
    });

    it("renders with custom max value", () => {
      render(<ProgressBar value={30} max={60} />);

      const progressBar = screen.getByRole("progressbar");
      expect(progressBar).toHaveAttribute("aria-valuemax", "60");
      expect(progressBar).toHaveAttribute("aria-valuenow", "30");
    });

    it("clamps value to max", () => {
      render(<ProgressBar value={150} max={100} />);

      const progressBar = screen.getByRole("progressbar");
      expect(progressBar).toHaveAttribute("aria-valuenow", "100");
    });

    it("clamps negative values to 0", () => {
      render(<ProgressBar value={-10} />);

      const progressBar = screen.getByRole("progressbar");
      expect(progressBar).toHaveAttribute("aria-valuenow", "0");
    });
  });

  describe("Percentage Calculation", () => {
    it("calculates correct percentage for value/max ratio", () => {
      const { container } = render(<ProgressBar value={50} max={100} showLabel />);

      expect(container.textContent).toContain("50%");
    });

    it("rounds percentage to nearest integer", () => {
      const { container } = render(<ProgressBar value={33} max={100} showLabel />);

      expect(container.textContent).toContain("33%");
    });

    it("handles edge case of 0%", () => {
      const { container } = render(<ProgressBar value={0} showLabel />);

      expect(container.textContent).toContain("0%");
    });

    it("handles edge case of 100%", () => {
      const { container } = render(<ProgressBar value={100} showLabel />);

      expect(container.textContent).toContain("100%");
    });
  });

  describe("Variants", () => {
    it("renders completed variant with green color", () => {
      const { container } = render(<ProgressBar value={100} variant="completed" />);

      const progressFill = container.querySelector(".bg-green-500");
      expect(progressFill).toBeInTheDocument();
    });

    it("renders processing variant with blue color", () => {
      const { container } = render(<ProgressBar value={50} variant="processing" />);

      const progressFill = container.querySelector(".bg-blue-500");
      expect(progressFill).toBeInTheDocument();
    });

    it("renders failed variant with red color", () => {
      const { container } = render(<ProgressBar value={25} variant="failed" />);

      const progressFill = container.querySelector(".bg-red-500");
      expect(progressFill).toBeInTheDocument();
    });

    it("renders default variant with gray color", () => {
      const { container } = render(<ProgressBar value={75} variant="default" />);

      const progressFill = container.querySelector(".bg-gray-500");
      expect(progressFill).toBeInTheDocument();
    });
  });

  describe("Label Display", () => {
    it("shows label when showLabel is true", () => {
      const { container } = render(<ProgressBar value={45} showLabel />);

      expect(container.textContent).toContain("45%");
    });

    it("hides label when showLabel is false", () => {
      const { container } = render(<ProgressBar value={45} showLabel={false} />);

      expect(container.textContent).not.toContain("45%");
    });

    it("displays label outside by default", () => {
      const { container } = render(<ProgressBar value={60} showLabel />);

      const outsideLabel = container.querySelector(".flex.items-center.gap-2");
      expect(outsideLabel).toBeInTheDocument();
    });

    it("displays label inside when labelPosition is 'inside'", () => {
      const { container } = render(
        <ProgressBar value={60} showLabel labelPosition="inside" />
      );

      const insideLabel = container.querySelector(".absolute.inset-0");
      expect(insideLabel).toBeInTheDocument();
      expect(insideLabel).toHaveTextContent("60%");
    });

    it("hides inside label when percentage is too low", () => {
      const { container } = render(
        <ProgressBar value={10} showLabel labelPosition="inside" />
      );

      const insideLabel = container.querySelector(".absolute.inset-0");
      expect(insideLabel).toBeNull();
    });
  });

  describe("Size Variants", () => {
    it("renders small size correctly", () => {
      const { container } = render(<ProgressBar value={50} size="sm" />);

      const progressContainer = container.querySelector(".h-1");
      expect(progressContainer).toBeInTheDocument();
    });

    it("renders medium size correctly", () => {
      const { container } = render(<ProgressBar value={50} size="md" />);

      const progressContainer = container.querySelector(".h-2");
      expect(progressContainer).toBeInTheDocument();
    });

    it("renders large size correctly", () => {
      const { container } = render(<ProgressBar value={50} size="lg" />);

      const progressContainer = container.querySelector(".h-3");
      expect(progressContainer).toBeInTheDocument();
    });
  });

  describe("Animation", () => {
    it("applies pulse animation when animated is true", () => {
      const { container } = render(
        <ProgressBar value={50} variant="processing" animated />
      );

      const progressFill = container.querySelector(".animate-pulse");
      expect(progressFill).toBeInTheDocument();
    });

    it("does not animate when animated is false", () => {
      const { container } = render(
        <ProgressBar value={50} variant="processing" animated={false} />
      );

      const progressFill = container.querySelector(".animate-pulse");
      expect(progressFill).toBeNull();
    });

    it("shows indeterminate animation for 0% progress", () => {
      const { container } = render(
        <ProgressBar value={0} variant="processing" animated />
      );

      const shimmer = container.querySelector(".animate-shimmer");
      expect(shimmer).toBeInTheDocument();
    });
  });

  describe("Accessibility", () => {
    it("has role='progressbar'", () => {
      render(<ProgressBar value={50} />);

      const progressBar = screen.getByRole("progressbar");
      expect(progressBar).toBeInTheDocument();
    });

    it("has aria-valuenow attribute", () => {
      render(<ProgressBar value={75} />);

      const progressBar = screen.getByRole("progressbar");
      expect(progressBar).toHaveAttribute("aria-valuenow", "75");
    });

    it("has aria-valuemin attribute", () => {
      render(<ProgressBar value={50} />);

      const progressBar = screen.getByRole("progressbar");
      expect(progressBar).toHaveAttribute("aria-valuemin", "0");
    });

    it("has aria-valuemax attribute", () => {
      render(<ProgressBar value={50} max={200} />);

      const progressBar = screen.getByRole("progressbar");
      expect(progressBar).toHaveAttribute("aria-valuemax", "200");
    });

    it("has descriptive aria-label", () => {
      render(<ProgressBar value={45} />);

      const progressBar = screen.getByRole("progressbar");
      expect(progressBar).toHaveAccessibleName(/progress.*45%/i);
    });
  });

  describe("CSS Classes", () => {
    it("applies custom className", () => {
      const { container } = render(
        <ProgressBar value={50} className="custom-class" />
      );

      const progressBar = container.querySelector(".custom-class");
      expect(progressBar).toBeInTheDocument();
    });

    it("includes transition classes for smooth animation", () => {
      const { container } = render(<ProgressBar value={50} />);

      const progressFill = container.querySelector(".transition-all");
      expect(progressFill).toBeInTheDocument();
    });

    it("applies rounded-full class for rounded ends", () => {
      const { container } = render(<ProgressBar value={50} />);

      const progressContainer = container.querySelector(".rounded-full");
      expect(progressContainer).toBeInTheDocument();
    });
  });

  describe("Variant Components", () => {
    it("CompletedProgressBar renders with completed variant", () => {
      const { container } = render(<CompletedProgressBar value={100} />);

      const progressFill = container.querySelector(".bg-green-500");
      expect(progressFill).toBeInTheDocument();
      expect(container.textContent).toContain("100%");
    });

    it("ProcessingProgressBar renders with processing variant and animation", () => {
      const { container } = render(<ProcessingProgressBar value={60} />);

      const progressFill = container.querySelector(".bg-blue-500");
      const animated = container.querySelector(".animate-pulse");
      expect(progressFill).toBeInTheDocument();
      expect(animated).toBeInTheDocument();
      expect(container.textContent).toContain("60%");
    });

    it("FailedProgressBar renders with failed variant", () => {
      const { container } = render(<FailedProgressBar value={30} />);

      const progressFill = container.querySelector(".bg-red-500");
      expect(progressFill).toBeInTheDocument();
    });

    it("ProcessingProgressBar can disable animation", () => {
      const { container } = render(
        <ProcessingProgressBar value={50} animated={false} />
      );

      const animated = container.querySelector(".animate-pulse");
      expect(animated).toBeNull();
    });
  });

  describe("CircularProgress", () => {
    it("renders circular progress correctly", () => {
      const { container } = render(<CircularProgress value={50} />);

      const svg = container.querySelector("svg");
      expect(svg).toBeInTheDocument();
    });

    it("shows percentage label in circular progress", () => {
      const { container } = render(<CircularProgress value={75} showLabel />);

      expect(container.textContent).toContain("75%");
    });

    it("hides label when showLabel is false", () => {
      const { container } = render(<CircularProgress value={75} showLabel={false} />);

      expect(container.textContent).not.toContain("75%");
    });

    it("renders with correct size", () => {
      const { container } = render(<CircularProgress value={50} size={64} />);

      const svg = container.querySelector("svg");
      expect(svg).toHaveAttribute("width", "64");
      expect(svg).toHaveAttribute("height", "64");
    });

    it("applies variant colors to circular progress", () => {
      const { container } = render(
        <CircularProgress value={50} variant="completed" />
      );

      const circle = container.querySelector("circle[stroke='#22c55e']");
      expect(circle).toBeInTheDocument();
    });
  });

  describe("Edge Cases", () => {
    it("handles very small values correctly", () => {
      const { container } = render(<ProgressBar value={0.5} showLabel />);

      expect(container.textContent).toContain("1%"); // Rounded up
    });

    it("handles fractional max values", () => {
      render(<ProgressBar value={0.5} max={1} />);

      const progressBar = screen.getByRole("progressbar");
      expect(progressBar).toHaveAttribute("aria-valuenow", "0.5");
    });

    it("handles zero max value gracefully", () => {
      render(<ProgressBar value={50} max={0} />);

      const progressBar = screen.getByRole("progressbar");
      expect(progressBar).toBeInTheDocument();
    });
  });
});
