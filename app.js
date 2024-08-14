import * as THREE from "three"

// ------------------------------------------------
// BASIC SETUP
// ------------------------------------------------

// Create an empty scene
var scene = new THREE.Scene();

// Create a basic perspective camera
var camera = new THREE.PerspectiveCamera( 75, window.innerWidth/window.innerHeight, 0.1, 1000 );
camera.position.z = 4;

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

// Create a Cube Mesh with basic material
var geometry = new THREE.BoxGeometry( 2, 0.1, 1 );
var material = new THREE.MeshBasicMaterial( { color: "#FFFFFF" } );

var cube = new THREE.Mesh( geometry, material );

const value = document.getElementById('value');

// Add cube to Scene
scene.add( cube );

const axesHelper = new THREE.AxesHelper(5);
scene.add( axesHelper );

var index = 0;

// Render Loop
function render() {
  requestAnimationFrame(render);
  
  if(sensor_data.length > 0) {
    // Get cursor position
    index = document.getElementById('time').valueAsNumber;
    // Print debug text
    value.innerHTML = index.toString() + " / " + sensor_data.length.toString() + 
                      " | X: " + sensor_data[index]['Rotation X'].toString() +
                      " | Y: " + sensor_data[index]['Rotation Y'].toString() +
                      " | Z: " + sensor_data[index]['Rotation Z'].toString();
    // Rotate object
    cube.rotation.x = sensor_data[index]['Rotation X'];
    cube.rotation.y = sensor_data[index]['Rotation Y'];
    cube.rotation.z = sensor_data[index]['Rotation Z'];
  }

  // Render the scene
  renderer.render(scene, camera);
};

render();
