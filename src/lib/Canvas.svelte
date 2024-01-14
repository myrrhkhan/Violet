<!-- Canvas.svelte -->
<style>
	@import '../styles.css';
	.canvas-container {
		position: relative;
		text-align: center;
	}

    .bottom-container {
        position: relative;
        text-align: center;
    }
	
	canvas {
		border: 2px solid var(--color-primary);
    	background-color: var(--color-secondary);
		display: block;
		margin: 0 auto;
	}
	
	button {
		color: var(--color-secondary);
    	background-color: var(--color-accent);
		display: block;
		margin-top: 10px;
		position: relative;
		left: 50%;
		transform: translateX(-50%);
		cursor: pointer;
		border-radius: 8px;
		border: 1px solid transparent;
		padding: 0.6em 1.2em;
		font-size: 1em;
		font-weight: 500;
		font-family: inherit;

		transition: border-color 0.25s;
		box-shadow: 0 2px 2px rgba(0, 0, 0, 0.2);
	}

	h2 {
		display: block;
        margin: 10px 0 0;
	}

	button:hover {
        border-color: var(--color-accent);
    }

	button:active {
		border-color: var(--color-accent);
		background-color: var(--color-primary);
	}
</style>

<script lang="ts">
	import { invoke } from "@tauri-apps/api/tauri"
    import { writable } from "svelte/store";
	let isDrawing = false;
	let context: CanvasRenderingContext2D;
	let canvas: HTMLCanvasElement;
	
	const canvasWidth = 800;  // Larger canvas size
	const canvasHeight = 200;
	
	let resultstring = writable("still here?");
	
	function startDrawing(event: MouseEvent) {
		isDrawing = true;
		const canvasRect = canvas.getBoundingClientRect();
		const offsetX = event.clientX - canvasRect.left;
		const offsetY = event.clientY - canvasRect.top;

		context = (event.target as HTMLCanvasElement).getContext('2d') as CanvasRenderingContext2D;
		context.beginPath();
		context.moveTo(offsetX, offsetY);
	}
	
	function draw(event: MouseEvent) {
		if (!isDrawing) return;
		const canvasRect = canvas.getBoundingClientRect();
		const offsetX = event.clientX - canvasRect.left;
		const offsetY = event.clientY - canvasRect.top;

		context.lineTo(offsetX, offsetY);
		context.stroke();
	}
	
	function stopDrawing() {
		isDrawing = false;
	}
	
	async function captureImage() {
		// Resize the canvas to the target dimensions
		const newCanvas: HTMLCanvasElement = document.createElement('canvas');
		const ctx = newCanvas.getContext('2d') as CanvasRenderingContext2D;
		newCanvas.width = 800;
		newCanvas.height = 200;
		
		ctx.fillStyle = 'white';
		ctx.fillRect(0, 0, canvasWidth, canvasHeight);
		ctx.drawImage(canvas, 0, 0);
		
		// Capture the image from the resized canvas
		const image: string = newCanvas.toDataURL('image/png').replace('data:image/png;base64,', '');
		
        // console.log(image);
		// Pass the image to the Rust side using Tauri's invoke function
		resultstring.set(await invoke('image_to_text', { image }) as string);
		console.log(resultstring);	
	}
</script>

<div class="canvas-container">
	<canvas
		bind:this={canvas}
		width={canvasWidth}
		height={canvasHeight}
		on:mousedown={startDrawing}
		on:mousemove={draw}
		on:mouseup={stopDrawing}
		on:mouseleave={stopDrawing}
	></canvas>

    <div class="bottom-container">
    	<button on:click={captureImage}>Capture and Analyze</button>
        <h2>{$resultstring}</h2>
    </div>

</div>
