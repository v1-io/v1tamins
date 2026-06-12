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

func fail(_ message: String) -> Never {
    print("ERROR: \(message)", to: &stderr)
    exit(1)
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

func render(_ page: CGPDFPage) -> CGImage? {
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
        return nil
    }

    context.setFillColor(NSColor.white.cgColor)
    context.fill(CGRect(x: 0, y: 0, width: width, height: height))
    context.saveGState()
    context.scaleBy(x: scale, y: scale)
    context.translateBy(x: -bounds.origin.x, y: -bounds.origin.y)
    context.drawPDFPage(page)
    context.restoreGState()

    return context.makeImage()
}

func recognize(_ image: CGImage) -> [String] {
    var lines: [String] = []
    let request = VNRecognizeTextRequest { request, _ in
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
        return ["[OCR failed: \(error)]"]
    }

    return lines
}

var output = ""

for pageIndex in 0..<pageCount {
    autoreleasepool {
        let pageNumber = pageIndex + 1
        guard let page = document.page(at: pageNumber), let image = render(page) else {
            output += "\n\n=== Page \(pageNumber) ===\n[OCR render failed]\n"
            return
        }

        let lines = recognize(image)
        output += "\n\n=== Page \(pageNumber) ===\n"
        output += lines.joined(separator: "\n")
        output += "\n"
    }

    if pageIndex == 0 || (pageIndex + 1) % 10 == 0 || pageIndex + 1 == pageCount {
        print("OCR \(pageIndex + 1)/\(pageCount)", to: &stderr)
    }
}

do {
    try output.write(to: outputURL, atomically: true, encoding: .utf8)
    print("wrote \(outputURL.path)")
} catch {
    fail("could not write output: \(error)")
}
