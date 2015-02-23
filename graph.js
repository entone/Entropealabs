var num_nodes = 66;
var num_children = 2;
var nodes = [];
var links = [];
var x_range = [0, 1000];
var y_range = [0, 1000];

function random(range){
    return Math.floor((Math.random()*range[1])+range[0]);
}

function cluster(parent, levels){
    console.log(levels);
    if(levels){
        levels-=1;
        for(var c=0; c<random([2, 3]); c++){
            var name = levels+"-"+c;
            console.log(name);
            var n = nodes.push({name:name});
            links.push({
                source:parent,
                target:n-1,
                value:random([1, 3]),
            });
            cluster(n-1, levels);
        }
    }
    return;
}

function tree(){
    var n = nodes.push({
        name:"Entropealabs"
    });
    cluster(n-1, 4);
}

function entropy(){

    for(var i=0; i < num_nodes; i++){
        nodes.push({
            name:i,
            group:Math.ceil(Math.random()*3),
        });
        for(var c=0; c<Math.ceil(Math.random()*3); c++){
            links.push({
                source:nodes.length-1,
                target:Math.floor(Math.random()*num_nodes),
                value:Math.ceil(Math.random()*5),
            });

        }
    }
}


//tree();
num_nodes = 55;
entropy();

var data = {
    nodes:nodes,
    links:links,
}

console.log(data);

var width = 1000,
    height = 1000;

var color = d3.scale.category20();

var force = d3.layout.force()
    .charge(-200)
    .linkDistance(250)
    .gravity(.04)
    .size([width, height]);

var svg = d3.select("body").append("svg")
    .attr("width", width)
    .attr("height", height);

force
  .nodes(data.nodes)
  .links(data.links)
  .linkStrength( function(d){ return Math.random(); })
  .start();

var link = svg.selectAll(".link")
    .data(data.links)
.enter().append("line")
    .attr("class", "link")
    .style("stroke-width", function(d) { return Math.sqrt(d.value); });

var node = svg.selectAll(".node")
    .data(data.nodes)
.enter().append("circle")
    .attr("class", "node")
    .attr("r", 9)
    .style("fill", function(d) { return 0x000000; })
    .call(force.drag);


force.on("tick", function() {
    link.attr("x1", function(d) { return d.source.x; })
        .attr("y1", function(d) { return d.source.y; })
        .attr("x2", function(d) { return d.target.x; })
        .attr("y2", function(d) { return d.target.y; });

    node.attr("cx", function(d) { return d.x; })
        .attr("cy", function(d) { return d.y; });
});
