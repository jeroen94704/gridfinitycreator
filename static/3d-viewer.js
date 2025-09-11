import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';

class GridfinityViewer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.model = null;
        this.animationId = null;
        this.updateTimer = null;
        this.lastFormData = {};
        
        this.init();
    }
    
    init() {
        // Create scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0xf0f0f0);
        
        // Setup camera
        const aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera = new THREE.PerspectiveCamera(45, aspect, 0.1, 1000);
        this.camera.position.set(100, 100, 100);
        
        // Setup renderer
        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.container.appendChild(this.renderer.domElement);
        
        // Add lights
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
        this.scene.add(ambientLight);
        
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
        directionalLight.position.set(50, 100, 50);
        directionalLight.castShadow = true;
        directionalLight.shadow.camera.near = 0.1;
        directionalLight.shadow.camera.far = 500;
        directionalLight.shadow.camera.left = -100;
        directionalLight.shadow.camera.right = 100;
        directionalLight.shadow.camera.top = 100;
        directionalLight.shadow.camera.bottom = -100;
        this.scene.add(directionalLight);
        
        // Add grid helper at origin
        const gridHelper = new THREE.GridHelper(200, 20, 0x888888, 0xcccccc);
        this.scene.add(gridHelper);
        
        // Setup controls
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.screenSpacePanning = false;
        this.controls.minDistance = 10;
        this.controls.maxDistance = 500;
        
        // Handle window resize
        window.addEventListener('resize', () => this.onWindowResize(), false);
        
        // Start animation loop
        this.animate();
    }
    
    onWindowResize() {
        const aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera.aspect = aspect;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    }
    
    animate() {
        this.animationId = requestAnimationFrame(() => this.animate());
        this.controls.update();
        this.renderer.render(this.scene, this.camera);
    }
    
    loadSTLFromBase64(base64Data) {
        // Remove previous model
        if (this.model) {
            this.scene.remove(this.model);
            if (this.model.geometry) this.model.geometry.dispose();
            if (this.model.material) this.model.material.dispose();
        }
        
        // Convert base64 to ArrayBuffer
        const binaryString = atob(base64Data);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        
        // Load STL
        const loader = new STLLoader();
        const geometry = loader.parse(bytes.buffer);
        
        // Create material
        const material = new THREE.MeshPhongMaterial({
            color: 0x2196f3,
            specular: 0x111111,
            shininess: 200,
            side: THREE.DoubleSide
        });
        
        // Create mesh
        this.model = new THREE.Mesh(geometry, material);
        this.model.castShadow = true;
        this.model.receiveShadow = true;
        
        // Rotate model to lie flat (rotate 90 degrees around X axis)
        this.model.rotation.x = -Math.PI / 2;
        
        // Center and position the model
        geometry.computeBoundingBox();
        const boundingBox = geometry.boundingBox.clone();
        
        // Get center point of original geometry
        const center = boundingBox.getCenter(new THREE.Vector3());
        
        // Position model: centered on X and Z, sitting on grid
        // After rotation: Y becomes Z, Z becomes -Y, X stays X
        this.model.position.set(
            -center.x,                   // Center on X axis  
            -boundingBox.min.z,         // Bottom sits on grid (original Z becomes Y after rotation)
            center.y                     // Center on Z axis (original Y becomes Z after rotation)
        );
        
        // Add to scene
        this.scene.add(this.model);
        
        // Adjust camera to fit model
        this.fitCameraToObject();
    }
    
    fitCameraToObject() {
        if (!this.model) return;
        
        const box = new THREE.Box3().setFromObject(this.model);
        const size = box.getSize(new THREE.Vector3());
        const center = box.getCenter(new THREE.Vector3());
        
        const maxDim = Math.max(size.x, size.y, size.z);
        const fov = this.camera.fov * (Math.PI / 180);
        const cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2)) * 1.5;
        
        this.camera.position.set(cameraZ, cameraZ, cameraZ);
        this.camera.lookAt(center);
        this.controls.target = center;
        this.controls.update();
    }
    
    showLoading() {
        // Add loading indicator
        if (!this.loadingDiv) {
            this.loadingDiv = document.createElement('div');
            this.loadingDiv.className = 'preview-loading';
            this.loadingDiv.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
            this.loadingDiv.style.position = 'absolute';
            this.loadingDiv.style.top = '50%';
            this.loadingDiv.style.left = '50%';
            this.loadingDiv.style.transform = 'translate(-50%, -50%)';
            this.loadingDiv.style.zIndex = '1000';
        }
        this.container.appendChild(this.loadingDiv);
    }
    
    hideLoading() {
        if (this.loadingDiv && this.loadingDiv.parentNode) {
            this.loadingDiv.parentNode.removeChild(this.loadingDiv);
        }
    }
    
    showError(message) {
        if (!this.errorDiv) {
            this.errorDiv = document.createElement('div');
            this.errorDiv.className = 'alert alert-danger';
            this.errorDiv.style.position = 'absolute';
            this.errorDiv.style.top = '10px';
            this.errorDiv.style.left = '10px';
            this.errorDiv.style.right = '10px';
            this.errorDiv.style.zIndex = '1000';
        }
        this.errorDiv.textContent = message;
        this.container.appendChild(this.errorDiv);
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            if (this.errorDiv && this.errorDiv.parentNode) {
                this.errorDiv.parentNode.removeChild(this.errorDiv);
            }
        }, 5000);
    }
    
    updatePreview(generatorId, formData, gridSpec) {
        // Cancel pending update
        if (this.updateTimer) {
            clearTimeout(this.updateTimer);
        }
        
        // Debounce updates by 500ms
        this.updateTimer = setTimeout(() => {
            this.fetchPreview(generatorId, formData, gridSpec);
        }, 500);
    }
    
    async fetchPreview(generatorId, formData, gridSpec) {
        this.showLoading();
        
        try {
            const response = await fetch('/preview', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    generator: generatorId,
                    formData: formData,
                    gridSpec: gridSpec
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.loadSTLFromBase64(result.data);
            } else {
                this.showError(result.error || 'Failed to generate preview');
            }
        } catch (error) {
            console.error('Preview error:', error);
            this.showError('Failed to load preview');
        } finally {
            this.hideLoading();
        }
    }
    
    dispose() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        
        if (this.updateTimer) {
            clearTimeout(this.updateTimer);
        }
        
        if (this.model) {
            this.scene.remove(this.model);
            if (this.model.geometry) this.model.geometry.dispose();
            if (this.model.material) this.model.material.dispose();
        }
        
        if (this.renderer) {
            this.renderer.dispose();
        }
        
        if (this.controls) {
            this.controls.dispose();
        }
    }
}

// Initialize viewer when DOM is ready
let viewer = null;

function initializeViewer(containerId) {
    if (viewer) {
        viewer.dispose();
    }
    viewer = new GridfinityViewer(containerId);
    return viewer;
}

// Function to collect form data
function collectFormData(formId) {
    const form = document.getElementById(formId + '_form');
    if (!form) return {};
    
    const formData = {};
    const inputs = form.querySelectorAll('input, select, textarea');
    
    inputs.forEach(input => {
        if (input.name && input.name !== 'csrf_token') {
            if (input.type === 'checkbox') {
                formData[input.name] = input.checked;
            } else if (input.type === 'radio') {
                if (input.checked) {
                    formData[input.name] = input.value;
                }
            } else {
                formData[input.name] = input.value;
            }
        }
    });
    
    return formData;
}

// Function to get grid specifications
function getGridSpec() {
    const gridSpec = {};
    
    // Try to get from advanced settings form if it exists
    const gridSizeX = document.querySelector('input[name="gridSizeX"]');
    const gridSizeY = document.querySelector('input[name="gridSizeY"]');
    const gridSizeZ = document.querySelector('input[name="gridSizeZ"]');
    
    if (gridSizeX && gridSizeY && gridSizeZ) {
        gridSpec.x = parseFloat(gridSizeX.value) || 42;
        gridSpec.y = parseFloat(gridSizeY.value) || 42;
        gridSpec.z = parseFloat(gridSizeZ.value) || 7;
    } else {
        // Use defaults or get from cookie
        const cookie = document.cookie.split('; ').find(row => row.startsWith('gridspec='));
        if (cookie) {
            const values = cookie.split('=')[1].split(',');
            gridSpec.x = parseFloat(values[0]) || 42;
            gridSpec.y = parseFloat(values[1]) || 42;
            gridSpec.z = parseFloat(values[2]) || 7;
        } else {
            gridSpec.x = 42;
            gridSpec.y = 42;
            gridSpec.z = 7;
        }
    }
    
    return gridSpec;
}

// Setup form change listeners
function setupFormListeners(generatorId) {
    const form = document.getElementById(generatorId + '_form');
    if (!form || !viewer) return;
    
    const updatePreview = () => {
        const formData = collectFormData(generatorId);
        const gridSpec = getGridSpec();
        viewer.updatePreview(generatorId, formData, gridSpec);
    };
    
    // Listen to all form inputs
    form.addEventListener('input', updatePreview);
    form.addEventListener('change', updatePreview);
    
    // Initial preview
    updatePreview();
}

// Export functions to global scope for backwards compatibility
window.GridfinityViewer = GridfinityViewer;
window.initializeViewer = initializeViewer;
window.setupFormListeners = setupFormListeners;
window.collectFormData = collectFormData;
window.getGridSpec = getGridSpec;