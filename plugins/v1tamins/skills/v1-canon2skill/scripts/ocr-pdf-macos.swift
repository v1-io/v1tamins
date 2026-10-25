#!/usr/bin/env swift
import AppKit
import Foundation
import Vision

struct StderrOutputStream: TextOutputStream {
    mutating func write(_ string: String) {
        FileHandle.standardError.write(Data(string.utf8))
    }
}

var stderr = StderrOutputStream()

func fail(_ message: String, code: Int32 = 1) -> Never {
    print("ERROR: \(message)", to: &stderr)
    exit(code)
}

enum OCRPageError: Error, CustomStringConvertible {
    case pageUnavailable
    case renderFailed
    case visionFailed(String)

    var stage: String {
        switch self {
        case .pageUnavailable:
            return "page"
        case .renderFailed:
            return "render"
        case .visionFailed:
            return "vision"
        }
    }

    var detail: String {
        switch self {
        case .pageUnavailable:
            return "PDF page could not be loaded"
        case .renderFailed:
            return "PDF page could not be rendered"
        case let .visionFailed(message):
            return message
        }
    }

    var description: String {
        "\(stage): \(detail)"
    }
}

struct PageFailure {
    let pageNumber: Int
    let stage: String
    let detail: String
}

func oneLine(_ value: String) -> String {
    value
        .replacingOccurrences(of: "\n", with: " ")
        .replacingOccurrences(of: "\r", with: " ")
        .trimmingCharacters(in: .whitespacesAndNewlines)
}

guard CommandLine.arguments.count == 3 else {
    fail("usage: ocr-pdf-macos.swift input.pdf output.txt")
}

let inputURL = URL(fileURLWithPath: CommandLine.arguments[1])
let outputURL = URL(fileURLWithPath: CommandLine.arguments[2])

guard let document = CGPDFDocument(inputURL as CFURL) else {
    fail("could not open PDF: \(inputURL.path)")
}

let pageCount = document.numberOfPages
guard pageCount > 0 else {
    fail("PDF has no pages: \(inputURL.path)")
}

func render(_ page: CGPDFPage) throws -> CGImage {
    let bounds = page.getBoxRect(.mediaBox)
    let scale: CGFloat = 2.0
    let width = max(1, Int(bounds.width * scale))
    let height = max(1, Int(bounds.height * scale))
    let colorSpace = CGColorSpaceCreateDeviceRGB()
    let bitmapInfo = CGImageAlphaInfo.premultipliedLast.rawValue

    guard let context = CGContext(
        data: nil,
        width: width,
        height: height,
        bitsPerComponent: 8,
        bytesPerRow: 0,
        space: colorSpace,
        bitmapInfo: bitmapInfo
    ) else {
        throw OCRPageError.renderFailed
    }

    context.setFillColor(NSColor.white.cgColor)
    context.fill(CGRect(x: 0, y: 0, width: width, height: height))
    context.saveGState()
    context.scaleBy(x: scale, y: scale)
    context.translateBy(x: -bounds.origin.x, y: -bounds.origin.y)
    context.drawPDFPage(page)
    context.restoreGState()

    guard let image = context.makeImage() else {
        throw OCRPageError.renderFailed
    }
    return image
}

func recognize(_ image: CGImage) throws -> [String] {
    var lines: [String] = []
    var requestError: Error?
    let request = VNRecognizeTextRequest { request, error in
        if let error {
            requestError = error
            return
        }
        let observations = request.results as? [VNRecognizedTextObservation] ?? []
        lines = observations.compactMap { observation in
            observation.topCandidates(1).first?.string
                .trimmingCharacters(in: .whitespacesAndNewlines)
        }.filter { !$0.isEmpty }
    }

    request.recognitionLevel = .accurate
    request.usesLanguageCorrection = true
    request.recognitionLanguages = ["en-US"]

    let handler = VNImageRequestHandler(cgImage: image, options: [:])
    do {
        try handler.perform([request])
    } catch {
        throw OCRPageError.visionFailed(oneLine(String(describing: error)))
    }

    if let requestError {
        throw OCRPageError.visionFailed(oneLine(String(describing: requestError)))
    }

    return lines
}

var output = ""
var failedPages: [PageFailure] = []
var successfulPageCount = 0

for pageIndex in 0..<pageCount {
    autoreleasepool {
        let pageNumber = pageIndex + 1
        do {
            guard let page = document.page(at: pageNumber) else {
                throw OCRPageError.pageUnavailable
            }
            let image = try render(page)
            let lines = try recognize(image)
            output += "\n\n=== Page \(pageNumber) ===\n"
            output += lines.joined(separator: "\n")
            output += "\n"
            successfulPageCount += 1
        } catch let error as OCRPageError {
            let failure = PageFailure(
                pageNumber: pageNumber,
                stage: error.stage,
                detail: oneLine(error.detail)
            )
            failedPages.append(failure)
            output += "\n\n=== Page \(pageNumber) ===\n"
            output += "[OCR \(failure.stage) failed: \(failure.detail)]\n"
        } catch {
            let failure = PageFailure(
                pageNumber: pageNumber,
                stage: "unknown",
                detail: oneLine(String(describing: error))
            )
            failedPages.append(failure)
            output += "\n\n=== Page \(pageNumber) ===\n"
            output += "[OCR failed: \(failure.detail)]\n"
        }
    }

    if pageIndex == 0 || (pageIndex + 1) % 10 == 0 || pageIndex + 1 == pageCount {
        print("OCR \(pageIndex + 1)/\(pageCount)", to: &stderr)
    }
}

if !failedPages.isEmpty {
    output += "\n\n=== OCR Failure Summary ===\n"
    output += "failed_pages=\(failedPages.count) total_pages=\(pageCount) "
    output += "successful_pages=\(successfulPageCount)\n"
    for failure in failedPages {
        output += "- Page \(failure.pageNumber): \(failure.stage): \(failure.detail)\n"
    }
}

do {
    try output.write(to: outputURL, atomically: true, encoding: .utf8)
    print("wrote \(outputURL.path)")
} catch {
    fail("could not write output: \(error)")
}

if !failedPages.isEmpty {
    let outcome = successfulPageCount == 0 ? "all pages failed" : "partial OCR"
    print(
        "OCR \(outcome): \(failedPages.count)/\(pageCount) page(s) failed",
        to: &stderr
    )
    fail("OCR \(outcome); retain the output and its data-gap summary", code: 2)
}
