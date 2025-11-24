import { generateText } from "ai"

export const maxDuration = 30

export async function POST(req: Request) {
  try {
    const { prompt, referenceImage } = await req.json()

    if (!prompt) {
      return Response.json({ error: "No prompt provided" }, { status: 400 })
    }

    const messages: any[] = []
    if (referenceImage) {
      messages.push({
        role: "user",
        content: [
          {
            type: "image",
            image: referenceImage,
          },
          {
            type: "text",
            text: prompt,
          },
        ],
      })
    }

    const result = await generateText({
      model: "google/gemini-2.5-flash-image-preview",
      prompt: messages.length > 0 ? undefined : prompt,
      messages: messages.length > 0 ? messages : undefined,
    })

    const images = []
    for (const file of result.files) {
      if (file.mediaType.startsWith("image/")) {
        images.push({
          base64: file.base64,
          mediaType: file.mediaType,
        })
      }
    }

    if (images.length > 0) {
      const imageDataUrl = `data:${images[0].mediaType};base64,${images[0].base64}`
      return Response.json({
        imageUrl: imageDataUrl,
        text: result.text,
        usage: result.usage,
      })
    } else {
      return Response.json({ error: "No image was generated" }, { status: 500 })
    }
  } catch (error) {
    console.error("Error generating image:", error)
    return Response.json({ error: "Failed to generate image" }, { status: 500 })
  }
}
