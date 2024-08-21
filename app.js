import * as THREE from "three"

// ------------------------------------------------
// BASIC SETUP
// ------------------------------------------------

// Create an empty scene
var scene = new THREE.Scene();

// Create a basic perspective camera
var camera = new THREE.PerspectiveCamera( 50, window.innerWidth/window.innerHeight, 0.1, 1000 );
camera.position.y = -5;
camera.rotation.x = Math.PI/2;
camera.rotation.z = -Math.PI/2;

// Create a renderer with Antialiasing
var renderer = new THREE.WebGLRenderer({antialias:true});
// Configure renderer clear color
renderer.setClearColor("#000000");
// Configure renderer size
renderer.setSize( window.innerWidth, window.innerHeight );
// Append Renderer to DOM
document.body.appendChild( renderer.domElement );

// ------------------------------------------------
// FUN STARTS HERE
// ------------------------------------------------
var cube;

const loader = new THREE.ObjectLoader();

loader.load(
	// resource URL
	"camera.json",

	// onLoad callback
	// Here the loaded data is assumed to be an object
	function ( obj ) {
    cube = obj;
		// Add the loaded object to the scene
		scene.add( cube );
	},

	// onProgress callback
	function ( xhr ) {
		console.log( (xhr.loaded / xhr.total * 100) + '% loaded' );
	},

	// onError callback
	function ( err ) {
		console.error( 'An error happened:' + err );
	}
);

const axesHelper = new THREE.AxesHelper(5);
scene.add( axesHelper );

var index = 0;

// Render Loop
function render() {
  requestAnimationFrame(render);
  
  if(sensor_data.length > 0) {
    // Get cursor position
    index = document.getElementById('time').valueAsNumber;

    let assiette = - sensor_data[index]['Rotation Z'] * 180 / Math.PI;
    let roulis = - sensor_data[index]['Rotation Y'] * 180 / Math.PI;
    let lacet = sensor_data[index]['Rotation X'] * 180 / Math.PI;

    // Print debug text
    value.innerHTML = index.toString() + " / " + sensor_data.length.toString() + 
                      " | assiette: " + assiette.toPrecision(3).toString() +
                      " | roulis: " + roulis.toPrecision(3).toString() +
                      " | lacet: " + lacet.toPrecision(3).toString();
    // Rotate object
    cube.rotation.x = sensor_data[index]['Rotation X'];
    cube.rotation.y = sensor_data[index]['Rotation Y'];
    cube.rotation.z = sensor_data[index]['Rotation Z'];
  }

  // Render the scene
  renderer.render(scene, camera);
};

render();
